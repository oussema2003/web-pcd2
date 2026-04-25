# Dans backend/core/views.py
import os
import uuid

from django.core.files.storage import default_storage
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["POST"])
def check_video_deepfake(request):
    video_file = request.FILES.get("video")
    if not video_file:
        return Response({"error": "Vidéo manquante."}, status=400)

    temp_dir = "temp/deepfake"
    temp_name = f"{uuid.uuid4().hex}_{video_file.name}"
    stored_name = default_storage.save(f"{temp_dir}/{temp_name}", video_file)
    file_path = default_storage.path(stored_name)

    try:
        from .ml.ai_service import analyze_candidate_video

        result = analyze_candidate_video(file_path)
        http_status = 200 if "error" not in result else 400
        return Response(result, status=http_status)
    except Exception as exc:
        return Response({"error": f"Erreur analyse deepfake: {exc!s}"}, status=500)
    finally:
        if default_storage.exists(stored_name):
            default_storage.delete(stored_name)
        elif os.path.exists(file_path):
            os.remove(file_path)