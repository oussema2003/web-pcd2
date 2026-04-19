from django.shortcuts import get_object_or_404
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

import logging

from groq import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

from accounts.models import User
from .models import Candidature, Offre
from .models import OffreQuestion
import json
import os
import sys
from pathlib import Path
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
from .match_score import (
    clean_llm_json_string,
    compute_correspondance,
    groq_match_raw_response,
    validate_match_payload,
)

logger = logging.getLogger(__name__)


def _lire_fichier_transcription(f) -> str:
    """Lit le contenu brut du FileField (.txt), via storage ou chemin disque."""
    if not f or not getattr(f, "name", None):
        return ""
    raw: bytes = b""
    try:
        with f.open("rb") as fh:
            raw = fh.read()
    except Exception:
        try:
            p = f.path
            if os.path.isfile(p):
                raw = Path(p).read_bytes()
        except (ValueError, NotImplementedError, OSError):
            return ""
    if not raw:
        return ""
    return raw.decode("utf-8-sig", errors="replace").strip()


def _normaliser_texte_transcription(text: str) -> str:
    """Retire caractères non imprimables (bruit encodage) tout en gardant retours à la ligne."""
    if not text:
        return ""
    return "".join(c for c in text if c.isprintable() or c in "\n\r\t").strip()


def _transcription_texte_video_uniquement(candidature: Candidature) -> str:
    """
    Texte vidéo pour le score : lit le fichier .txt ET le champ DB, garde la version la plus longue
    (souvent le .txt complet vs un extrait en base). Les réponses au formulaire ne sont pas incluses.
    """
    db = (candidature.transcription or "").strip()
    file_t = ""
    f = candidature.transcription_file
    if f and getattr(f, "name", None):
        file_t = _lire_fichier_transcription(f)
    chosen = file_t if len(file_t) >= len(db) else db
    return _normaliser_texte_transcription(chosen)


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


class CandidatureAIAnalysisView(APIView):
    """
    Analyse IA : stress/émotion sur l'audio MP3 de la candidature + score de correspondance entre
    la description de l'offre et la transcription vidéo uniquement (fichier .txt / champ transcription),
    sans les réponses au formulaire.
    """

    permission_classes = [permissions.IsAuthenticated, IsRecruiter]

    def get(self, request, pk: int):
        candidature = get_object_or_404(
            Candidature.objects.select_related("offre"), pk=pk
        )
        if candidature.offre.created_by != request.user:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

        if not candidature.audio:
            return Response(
                {
                    "detail": "Aucun fichier audio (MP3) disponible pour cette candidature. "
                    "L'audio est extrait automatiquement à partir de la vidéo lors du dépôt."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        audio_path = candidature.audio.path
        if not os.path.isfile(audio_path):
            return Response(
                {"detail": "Fichier audio introuvable sur le serveur."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .audio_analysis import analyser_stress

            analyse_vocale = analyser_stress(audio_path)
        except ImportError as e:
            return Response(
                {
                    "detail": (
                        "Modules d'analyse vocale absents dans l'environnement du serveur Django "
                        "(torch, transformers, librosa, etc.). "
                        f"Python utilisé par ce processus : {sys.executable}. "
                        "Installez dans ce même interpréteur, puis redémarrez le serveur : "
                        f'"{sys.executable}" -m pip install -r requirements.txt '
                        f"(à lancer depuis le dossier backend). Détail : {e!s}"
                    ),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de l'analyse vocale : {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        candidate_text = _transcription_texte_video_uniquement(candidature)
        logger.debug(
            "analyse-ia candidature=%s transcription_chars=%s (fichier+champ, plus long retenu)",
            pk,
            len(candidate_text),
        )
        api_key = getattr(settings, "GROQ_API_KEY", "") or ""
        model_name = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile"

        correspondance: dict
        correspondance_source = "local"
        correspondance_note: str | None = None

        def _local_fallback(note: str | None = None) -> None:
            nonlocal correspondance, correspondance_source, correspondance_note
            correspondance = compute_correspondance(
                candidature.offre.description,
                candidate_text if candidate_text else None,
                None,
            )
            correspondance_source = "local"
            correspondance_note = note

        # Dès qu'une clé Groq est configurée, on tente le modèle ; sinon score local uniquement.
        if api_key:
            try:
                raw = groq_match_raw_response(
                    candidature.offre.description,
                    candidate_text,
                    api_key,
                    model_name=model_name,
                )
                cleaned = clean_llm_json_string(raw)
                payload = json.loads(cleaned)
                correspondance = validate_match_payload(payload)
                correspondance_source = "groq"
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(
                    "Réponse Groq (score correspondance) non exploitable : %s",
                    e,
                    exc_info=True,
                )
                _local_fallback(
                    "La réponse de l’IA n’a pas pu être interprétée ; score estimé par comparaison textuelle locale."
                )
            except RateLimitError:
                logger.warning(
                    "Limite de débit Groq (modèle %s) ; score de correspondance en mode local.",
                    model_name,
                )
                _local_fallback(
                    "Limite de requêtes Groq atteinte. Réessayez dans une minute ou vérifiez votre plan. "
                    "Score affiché : estimation locale."
                )
            except AuthenticationError:
                logger.warning("Clé API Groq refusée.")
                _local_fallback(
                    "Clé API Groq refusée (invalide ou révoquée). Vérifiez GROQ_API_KEY sur la machine qui lance Django. "
                    "Score estimé en local."
                )
            except BadRequestError as e:
                logger.warning("Requête Groq refusée : %s", e)
                _local_fallback(
                    f"Requête Groq refusée (souvent modèle ou format). Vérifiez GROQ_MODEL (actuel : {model_name}). "
                    "Score estimé en local."
                )
            except NotFoundError:
                logger.warning("Modèle Groq introuvable : %s", model_name)
                _local_fallback(
                    f"Modèle « {model_name} » introuvable sur Groq. Consultez la liste des modèles sur console.groq.com. "
                    "Score estimé en local."
                )
            except PermissionDeniedError as e:
                logger.warning("Accès Groq refusé : %s", e)
                _local_fallback(
                    "Accès refusé par Groq. Vérifiez les droits de la clé API. Score estimé en local."
                )
            except (APIConnectionError, APITimeoutError) as e:
                logger.warning("Réseau Groq : %s", e)
                _local_fallback(
                    "Impossible de joindre l’API Groq (réseau ou délai dépassé). Réessayez plus tard. Score estimé en local."
                )
            except Exception:
                logger.exception("Erreur lors de l'appel Groq (score correspondance)")
                _local_fallback(
                    "Erreur lors de l’appel Groq. Réessayez plus tard. Score estimé en local."
                )
        else:
            correspondance = compute_correspondance(
                candidature.offre.description,
                candidate_text if candidate_text else None,
                None,
            )

        payload_corr = {
            "titre": "Score de Correspondance",
            "score": correspondance["score"],
            "justification": correspondance["justification"],
            "source": correspondance_source,
        }
        if correspondance_note:
            payload_corr["note"] = correspondance_note

        return Response(
            {
                "analyse_vocale": {
                    "titre": "Analyse Vocale (Stress & Émotion)",
                    "arousal": analyse_vocale["arousal"],
                    "dominance": analyse_vocale["dominance"],
                    "valence": analyse_vocale["valence"],
                    "etat_stress": analyse_vocale["etat"],
                },
                "correspondance": payload_corr,
            }
        )

