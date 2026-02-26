from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Candidature, Offre
from .models import OffreQuestion
import json


class OffreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offre
        fields = ["id", "titre", "description", "localisation", "salaire", "date_creation"]


class OffreQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffreQuestion
        fields = ["id", "text", "required", "input_type", "order"]


class OffreDetailSerializer(OffreSerializer):
    has_applied = serializers.SerializerMethodField()
    questions = OffreQuestionSerializer(many=True, read_only=True)

    class Meta(OffreSerializer.Meta):
        fields = OffreSerializer.Meta.fields + ["has_applied", "questions"]

    def get_has_applied(self, obj: Offre) -> bool:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return Candidature.objects.filter(offre=obj, candidat=user).exists()


class CandidatureForCandidateSerializer(serializers.ModelSerializer):
    offre = OffreSerializer()
    answers = serializers.JSONField(required=False)

    class Meta:
        model = Candidature
        fields = ["id", "offre", "date_postulation", "statut", "nom", "prenom", "email", "telephone", "cv", "video", "answers"]


class CandidatureForRecruiterSerializer(serializers.ModelSerializer):
    candidat = UserSerializer()
    answers = serializers.JSONField(required=False)

    class Meta:
        model = Candidature
        fields = ["id", "candidat", "offre", "date_postulation", "statut", "nom", "prenom", "email", "telephone", "cv", "video", "answers"]


class CandidatureStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidature
        fields = ["statut"]

