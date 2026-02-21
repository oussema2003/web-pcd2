from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def api_root(request):
    return HttpResponse("Talent Connect API is running. See /api/ and /api/auth/.")


urlpatterns = [
    path("", api_root),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/", include("jobs.urls")),
]

