from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Candidature, Offre


class OffreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offre
        fields = ["id", "titre", "description", "localisation", "salaire", "date_creation"]


class OffreDetailSerializer(OffreSerializer):
    has_applied = serializers.SerializerMethodField()

    class Meta(OffreSerializer.Meta):
        fields = OffreSerializer.Meta.fields + ["has_applied"]

    def get_has_applied(self, obj: Offre) -> bool:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return Candidature.objects.filter(offre=obj, candidat=user).exists()


class CandidatureForCandidateSerializer(serializers.ModelSerializer):
    offre = OffreSerializer()

    class Meta:
        model = Candidature
        fields = ["id", "offre", "date_postulation", "statut"]


class CandidatureForRecruiterSerializer(serializers.ModelSerializer):
    candidat = UserSerializer()

    class Meta:
        model = Candidature
        fields = ["id", "candidat", "offre", "date_postulation", "statut"]


class CandidatureStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidature
        fields = ["statut"]

