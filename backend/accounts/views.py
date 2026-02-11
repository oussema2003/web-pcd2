from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = LoginSerializer.get_tokens_for_user(user)
        data = {
            "user": UserSerializer(user).data,
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        }
        return Response(data, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class CandidatesListView(APIView):
    """
    Liste tous les utilisateurs ayant le rôle candidat.
    Accessible uniquement aux RH.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Roles.RH:
            return Response({"detail": "Accès réservé aux recruteurs."}, status=status.HTTP_403_FORBIDDEN)
        candidates = User.objects.filter(role=User.Roles.CANDIDATE)
        return Response(UserSerializer(candidates, many=True).data)


class LogoutView(APIView):
    """
    Pour JWT, la déconnexion côté client consiste à supprimer les tokens.
    Ce endpoint est fourni pour cohérence, mais ne fait qu'acquitter la demande.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)

