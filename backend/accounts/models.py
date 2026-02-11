from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        RH = "rh", "Recruteur (RH)"
        CANDIDATE = "candidate", "Candidat"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Roles.choices)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.email} ({self.role})"

