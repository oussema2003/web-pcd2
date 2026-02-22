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
    
    # Personal Information
    nom = models.CharField(max_length=255, null=True, blank=True)
    prenom = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    
    # Files
    cv = models.FileField(upload_to="candidatures/cv/", null=True, blank=True)
    video = models.FileField(upload_to="candidatures/video/", null=True, blank=True)
    # Store answers to dynamic application questions as JSON: { question_id: answer }
    answers = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ("offre", "candidat")
        ordering = ["-date_postulation"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.candidat} -> {self.offre}"


class OffreQuestion(models.Model):
    class InputType(models.TextChoices):
        TEXT = "text", "Texte"
        TEXTAREA = "textarea", "Paragraphe"
        FILE = "file", "Fichier"

    offre = models.ForeignKey(Offre, related_name="questions", on_delete=models.CASCADE)
    text = models.CharField(max_length=1024)
    required = models.BooleanField(default=False)
    input_type = models.CharField(max_length=20, choices=InputType.choices, default=InputType.TEXT)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Question for {self.offre}: {self.text[:50]}"

