from django.contrib import admin

from .models import Candidature, Offre


@admin.register(Offre)
class OffreAdmin(admin.ModelAdmin):
    list_display = ["titre", "localisation", "salaire", "created_by", "date_creation"]
    list_filter = ["date_creation", "localisation"]
    search_fields = ["titre", "description", "localisation"]
    readonly_fields = ["date_creation"]
    date_hierarchy = "date_creation"
    
    fieldsets = (
        ("Informations générales", {
            "fields": ("titre", "description", "localisation", "salaire")
        }),
        ("Création", {
            "fields": ("created_by", "date_creation")
        }),
    )


@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ["candidat", "offre", "statut", "date_postulation"]
    list_filter = ["statut", "date_postulation"]
    search_fields = ["candidat__email", "candidat__username", "offre__titre"]
    readonly_fields = ["date_postulation"]
    date_hierarchy = "date_postulation"
    
    fieldsets = (
        ("Candidature", {
            "fields": ("offre", "candidat", "statut")
        }),
        ("Dates", {
            "fields": ("date_postulation",)
        }),
    )
