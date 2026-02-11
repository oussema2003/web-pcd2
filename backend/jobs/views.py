from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from .models import Candidature, Offre
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
        return Response(OffreSerializer(offre).data, status=status.HTTP_201_CREATED)


class OffreDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, pk: int) -> Offre:
        return get_object_or_404(Offre, pk=pk)

    def get(self, request, pk: int):
        offre = self.get_object(pk)
        serializer = OffreDetailSerializer(offre, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk: int):
        if not request.user.is_authenticated or request.user.role != User.Roles.RH:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        offre = self.get_object(pk)
        if offre.created_by != request.user:
            return Response({"detail": "Vous n'êtes pas le créateur de cette offre."}, status=status.HTTP_403_FORBIDDEN)
        serializer = OffreSerializer(offre, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

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
        candidature, created = Candidature.objects.get_or_create(offre=offre, candidat=request.user)
        if not created:
            return Response({"detail": "Vous avez déjà postulé à cette offre."}, status=status.HTTP_400_BAD_REQUEST)
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

