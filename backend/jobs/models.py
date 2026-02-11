from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Offre(models.Model):
    titre = models.CharField(max_length=255)
    description = models.TextField()
    localisation = models.CharField(max_length=255)
    salaire = models.CharField(max_length=100, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name="offres", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.titre


class Candidature(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        ACCEPTEE = "acceptee", "Acceptée"
        REFUSEE = "refusee", "Refusée"

    offre = models.ForeignKey(Offre, related_name="candidatures", on_delete=models.CASCADE)
    candidat = models.ForeignKey(User, related_name="candidatures", on_delete=models.CASCADE)
    date_postulation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)

    class Meta:
        unique_together = ("offre", "candidat")
        ordering = ["-date_postulation"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.candidat} -> {self.offre}"

