from django.shortcuts import get_object_or_404
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from .models import Candidature, Offre
from .models import OffreQuestion
import json
import os
import time
import requests
from moviepy.editor import VideoFileClip
from .serializers import (
    CandidatureForCandidateSerializer,
    CandidatureForRecruiterSerializer,
    CandidatureStatusUpdateSerializer,
    OffreDetailSerializer,
    OffreSerializer,
)


class IsRecruiter(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Roles.RH)


class IsCandidate(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == User.Roles.CANDIDATE
        )


class OffreListView(APIView):
    """
    Liste publique des offres.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        offres = Offre.objects.all()
        return Response(OffreSerializer(offres, many=True).data)


class MyOffresView(APIView):
    """
    Liste et création des offres pour un recruteur.
    """

    permission_classes = [permissions.IsAuthenticated, IsRecruiter]

    def get(self, request):
        offres = Offre.objects.filter(created_by=request.user)
        return Response(OffreSerializer(offres, many=True).data)

    def post(self, request):
        serializer = OffreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offre = serializer.save(created_by=request.user)

        # Optionally accept a `questions` array when creating an offre
        # Each question: { text, required?, input_type? }
        questions = request.data.get("questions")
        if questions and isinstance(questions, list):
            for idx, q in enumerate(questions):
                try:
                    # if body was sent as JSON string, try to parse each item
                    if isinstance(q, str):
                        q = json.loads(q)
                except Exception:
                    q = {"text": str(q)}
                OffreQuestion.objects.create(
                    offre=offre,
                    text=q.get("text", ""),
                    required=bool(q.get("required", False)),
                    input_type=q.get("input_type", OffreQuestion.InputType.TEXT),
                    order=idx,
                )

        return Response(OffreDetailSerializer(offre, context={"request": request}).data, status=status.HTTP_201_CREATED)


class OffreDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, pk: int) -> Offre:
        return get_object_or_404(Offre, pk=pk)

    def get(self, request, pk: int):
        offre = self.get_object(pk)
        # Serializing with related objects (questions) may fail if DB migrations
        # for the new models haven't been applied yet. Handle that gracefully
        # so the frontend can still show the basic offer instead of 500.
        try:
            serializer = OffreDetailSerializer(offre, context={"request": request})
            return Response(serializer.data)
        except Exception:
            # Fall back to basic OffreSerializer to avoid exposing internal errors
            basic = OffreSerializer(offre)
            return Response(basic.data)

    def put(self, request, pk: int):
        if not request.user.is_authenticated or request.user.role != User.Roles.RH:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        offre = self.get_object(pk)
        if offre.created_by != request.user:
            return Response({"detail": "Vous n'êtes pas le créateur de cette offre."}, status=status.HTTP_403_FORBIDDEN)
        serializer = OffreSerializer(offre, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Allow updating questions when editing an offer. Expect `questions` as a list.
        questions = request.data.get("questions")
        if questions is not None and isinstance(questions, list):
            # Simple strategy: remove existing questions and recreate from provided list
            offre.questions.all().delete()
            for idx, q in enumerate(questions):
                try:
                    if isinstance(q, str):
                        q = json.loads(q)
                except Exception:
                    q = {"text": str(q)}
                OffreQuestion.objects.create(
                    offre=offre,
                    text=q.get("text", ""),
                    required=bool(q.get("required", False)),
                    input_type=q.get("input_type", OffreQuestion.InputType.TEXT),
                    order=idx,
                )

        # Return updated detail including questions
        return Response(OffreDetailSerializer(offre, context={"request": request}).data)

    def delete(self, request, pk: int):
        if not request.user.is_authenticated or request.user.role != User.Roles.RH:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        offre = self.get_object(pk)
        if offre.created_by != request.user:
            return Response({"detail": "Vous n'êtes pas le créateur de cette offre."}, status=status.HTTP_403_FORBIDDEN)
        offre.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def generate_transcription_for_candidature(candidature: Candidature) -> None:
    """
    Envoie le fichier audio de la candidature à AssemblyAI pour produire
    une transcription texte et la stocker dans `transcription` + un fichier .txt.
    Cette fonction est appelée de manière synchrone après la création.
    """
    api_key = getattr(settings, "ASSEMBLYAI_API_KEY", None)
    if not api_key:
        print("[assemblyai] Aucune clé API configurée, transcription ignorée.")
        return
    if not candidature.audio:
        return

    audio_path = candidature.audio.path

    headers = {
        "authorization": api_key,
        "content-type": "application/json",
    }

    # 1) Upload du fichier audio
    upload_url = "https://api.assemblyai.com/v2/upload"
    try:
        with open(audio_path, "rb") as f:
            upload_resp = requests.post(
                upload_url, headers={"authorization": api_key}, data=f, timeout=60
            )
    except Exception as e:
        print(f"[assemblyai] Erreur lors de l'upload audio: {e}")
        return

    if upload_resp.status_code != 200:
        print(f"[assemblyai] Upload refusé: {upload_resp.status_code} {upload_resp.text}")
        return

    audio_url = upload_resp.json().get("upload_url")
    if not audio_url:
        print("[assemblyai] URL d'upload manquante dans la réponse.")
        return

    # 2) Création de la demande de transcription
    transcript_request = {
        "audio_url": audio_url,
        "language_code": "fr",
        "speech_models": ["universal-3-pro"],
    }

    try:
        create_resp = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            json=transcript_request,
            headers=headers,
            timeout=30,
        )
    except Exception as e:
        print(f"[assemblyai] Erreur lors de la création de la transcription: {e}")
        return

    if create_resp.status_code not in (200, 201):
        print(f"[assemblyai] Création de transcription refusée: {create_resp.status_code} {create_resp.text}")
        return

    transcript_id = create_resp.json().get("id")
    if not transcript_id:
        print("[assemblyai] ID de transcription manquant dans la réponse.")
        return

    # 3) Polling jusqu'à complétion (limite de temps raisonnable)
    status_value = ""
    transcript_text = None
    for _ in range(20):  # ~20 * 3s = 60s max
        try:
            status_resp = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers=headers,
                timeout=15,
            )
        except Exception as e:
            print(f"[assemblyai] Erreur lors de la récupération du statut: {e}")
            return

        if status_resp.status_code != 200:
            print(f"[assemblyai] Statut refusé: {status_resp.status_code} {status_resp.text}")
            return

        body = status_resp.json()
        status_value = body.get("status")

        if status_value == "completed":
            transcript_text = body.get("text") or ""
            break
        if status_value == "error":
            print(f"[assemblyai] Erreur transcription: {body.get('error')}")
            return

        time.sleep(3)

    if transcript_text:
        candidature.transcription = transcript_text

        # Enregistrer aussi la transcription dans un fichier .txt
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        rel_path = f"candidatures/transcriptions/{base_name}.txt"
        file_content = ContentFile(transcript_text.encode("utf-8"))
        saved_path = default_storage.save(rel_path, file_content)

        candidature.transcription_file.name = saved_path
        candidature.save(update_fields=["audio", "transcription", "transcription_file", "answers"])


class ApplyOffreView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def post(self, request, pk: int):
        offre = get_object_or_404(Offre, pk=pk)
        
        # Check if already applied
        if Candidature.objects.filter(offre=offre, candidat=request.user).exists():
            return Response({"detail": "Vous avez déjà postulé à cette offre."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get form data
        nom = request.data.get("nom")
        prenom = request.data.get("prenom")
        email = request.data.get("email")
        telephone = request.data.get("telephone")
        cv = request.FILES.get("cv")
        video = request.FILES.get("video")
        # Answers to dynamic questions can be sent as a JSON string or dict under "answers"
        answers_raw = request.data.get("answers")
        answers = None
        if answers_raw:
            if isinstance(answers_raw, str):
                try:
                    answers = json.loads(answers_raw)
                except Exception:
                    answers = {"_raw": answers_raw}
            elif isinstance(answers_raw, dict):
                answers = answers_raw
        
        # Validate required fields (base fields remain required)
        if not all([nom, prenom, email, telephone, cv, video]):
            return Response(
                {"detail": "Tous les champs sont obligatoires."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create candidature
        candidature = Candidature.objects.create(
            offre=offre,
            candidat=request.user,
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            cv=cv,
            video=video,
        )

        # Convert video to MP3 and store alongside it
        if candidature.video:
            try:
                video_path = candidature.video.path
                base, _ = os.path.splitext(video_path)
                audio_path = base + ".mp3"

                # Extract audio track to MP3 using moviepy
                with VideoFileClip(video_path) as clip:
                    if clip.audio is not None:
                        clip.audio.write_audiofile(audio_path, codec="mp3")

                        # Attach generated MP3 file to the candidature.audio field
                        with open(audio_path, "rb") as f:
                            candidature.audio.save(os.path.basename(audio_path), File(f), save=False)
                    else:
                        print(f"[moviepy] Aucun flux audio dans la vidéo: {video_path}")
            except Exception as e:
                # Log the error so we pouvons diagnostiquer le problème
                print(f"[moviepy] Erreur lors de la conversion vidéo->MP3 pour {video_path}: {e}")

        # Save answers if provided, then persist any audio field updates
        if answers:
            candidature.answers = answers

        candidature.save()

        # Optionally generate a transcription of the audio track
        generate_transcription_for_candidature(candidature)
        
        return Response(
            CandidatureForCandidateSerializer(candidature).data,
            status=status.HTTP_201_CREATED,
        )


class MyCandidaturesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get(self, request):
        candidatures = Candidature.objects.filter(candidat=request.user).select_related("offre")
        serializer = CandidatureForCandidateSerializer(candidatures, many=True)
        return Response(serializer.data)


class OffreCandidaturesView(APIView):
    """
    Liste des candidatures pour une offre donnée (côté recruteur).
    """

    permission_classes = [permissions.IsAuthenticated, IsRecruiter]

    def get(self, request, pk: int):
        offre = get_object_or_404(Offre, pk=pk, created_by=request.user)
        candidatures = offre.candidatures.select_related("candidat")
        serializer = CandidatureForRecruiterSerializer(candidatures, many=True)
        return Response(serializer.data)


class CandidatureStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsRecruiter]

    def patch(self, request, pk: int):
        candidature = get_object_or_404(Candidature, pk=pk)
        if candidature.offre.created_by != request.user:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CandidatureStatusUpdateSerializer(candidature, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CandidatureForRecruiterSerializer(candidature).data)

