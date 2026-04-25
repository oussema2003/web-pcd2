from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import include, path

from .views import check_video_deepfake


def api_root(request):
    return HttpResponse("Talent Connect API is running. See /api/ and /api/auth/.")


urlpatterns = [
    path("", api_root),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/", include("jobs.urls")),
    path("api/check-video-deepfake/", check_video_deepfake, name="check-video-deepfake"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

