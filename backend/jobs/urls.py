from django.urls import path

from .views import (
    ApplyOffreView,
    CandidatureStatusUpdateView,
    MyCandidaturesView,
    MyOffresView,
    OffreCandidaturesView,
    OffreDetailView,
    OffreListView,
)

urlpatterns = [
    path("offres/", OffreListView.as_view(), name="offres-list"),
    path("offres/mine/", MyOffresView.as_view(), name="offres-mine"),
    path("offres/<int:pk>/", OffreDetailView.as_view(), name="offres-detail"),
    path("offres/<int:pk>/postuler/", ApplyOffreView.as_view(), name="offres-apply"),
    path("offres/<int:pk>/candidatures/", OffreCandidaturesView.as_view(), name="offres-candidatures"),
    path("candidatures/me/", MyCandidaturesView.as_view(), name="candidatures-me"),
    path("candidatures/<int:pk>/", CandidatureStatusUpdateView.as_view(), name="candidatures-update"),
]

