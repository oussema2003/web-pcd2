from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from .models import Candidature, Offre
from .models import OffreQuestion
import json
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
            video=video
        )

        # Save answers if provided
        if answers:
            candidature.answers = answers
            candidature.save()
        
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

