from __future__ import annotations

import os
from typing import List

from django.conf import settings
SEQUENCE_LENGTH = 15
cv2 = None
np = None
torch = None
MTCNN = None
CNN_Transformer_Deepfake = None
device = None
detector = None
face_cascade = None
detector_backend = "none"


def _resolve_model_path() -> str:
    ml_dir = os.path.join(settings.BASE_DIR, "core", "ml")
    candidates = [
        os.path.join(ml_dir, "deepfake_model.pth"),
        os.path.join(ml_dir, "deepfake_weights.pth"),
        os.path.join(ml_dir, "ton_modele_poids.pth"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Aucun fichier de poids Deepfake (.pth) trouvé dans core/ml/.")


MODEL_PATH = None
model = None
transform = None
imagenet_mean = None
imagenet_std = None


def _load_runtime_dependencies() -> str | None:
    global cv2, np, torch, MTCNN, CNN_Transformer_Deepfake, device, detector, face_cascade, detector_backend
    global transform, imagenet_mean, imagenet_std

    if cv2 is not None and np is not None and torch is not None and imagenet_mean is not None and imagenet_std is not None:
        return None

    try:
        import cv2 as _cv2
        import numpy as _np
        import torch as _torch

        from .architecture import CNN_Transformer_Deepfake as _CNN_Transformer_Deepfake
    except Exception as exc:
        return f"Dépendances IA manquantes: {exc!s}"

    _MTCNN = None
    try:
        from mtcnn import MTCNN as _ImportedMTCNN

        _MTCNN = _ImportedMTCNN
    except Exception:
        _MTCNN = None

    cv2 = _cv2
    np = _np
    torch = _torch
    MTCNN = _MTCNN
    CNN_Transformer_Deepfake = _CNN_Transformer_Deepfake
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if MTCNN is not None:
        detector = MTCNN()
        detector_backend = "mtcnn"
    else:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            return "Aucun detecteur de visage disponible (MTCNN/TensorFlow absent et cascade OpenCV indisponible)."
        detector_backend = "haar"
    imagenet_mean = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(3, 1, 1)
    imagenet_std = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(3, 1, 1)
    return None


def _extract_face_tensor(frame_bgr):
    try:
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        if detector_backend == "mtcnn":
            faces = detector.detect_faces(rgb_frame)
            if not faces:
                return None
            best_face = max(faces, key=lambda f: f.get("confidence", 0.0))
            x, y, w, h = best_face["box"]
        elif detector_backend == "haar":
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
            if len(faces) == 0:
                return None
            x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
        else:
            return None

        x = max(0, int(x))
        y = max(0, int(y))
        w = max(1, int(w))
        h = max(1, int(h))
        x2 = min(rgb_frame.shape[1], x + w)
        y2 = min(rgb_frame.shape[0], y + h)
        if x2 <= x or y2 <= y:
            return None

        face_crop = rgb_frame[y:y2, x:x2]
        resized = cv2.resize(face_crop, (224, 224), interpolation=cv2.INTER_LINEAR)
        face_tensor = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
        face_tensor = (face_tensor - imagenet_mean) / imagenet_std
        return face_tensor
    except Exception:
        return None


def _frame_indices_for_segment(start: int, end: int, count: int):
    if end <= start:
        end = start + 1
    return np.linspace(start, end - 1, num=count, dtype=int)


def analyze_candidate_video(video_path):
    global model

    dependency_error = _load_runtime_dependencies()
    if dependency_error:
        return {"error": dependency_error}

    try:
        if MODEL_PATH is None:
            globals()["MODEL_PATH"] = _resolve_model_path()
        if model is None:
            model = CNN_Transformer_Deepfake()
            model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
            model.to(device)
            model.eval()
    except Exception as exc:
        return {"error": f"Impossible de charger le modèle Deepfake: {exc!s}"}

    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Impossible d'ouvrir la vidéo."}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            return {"error": "Vidéo invalide ou vide."}

        sequence_count = max(1, total_frames // SEQUENCE_LENGTH)
        segment_edges = np.linspace(0, total_frames, num=sequence_count + 1, dtype=int)

        real_votes = 0
        fake_votes = 0
        confidences: List[float] = []
        valid_sequences = 0

        with torch.no_grad():
            for i in range(sequence_count):
                start = int(segment_edges[i])
                end = int(segment_edges[i + 1])
                frame_indices = _frame_indices_for_segment(start, end, SEQUENCE_LENGTH)

                faces_for_sequence = []
                for frame_idx in frame_indices:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
                    ok, frame = cap.read()
                    if not ok:
                        continue
                    face_tensor = _extract_face_tensor(frame)
                    if face_tensor is not None:
                        faces_for_sequence.append(face_tensor)

                if not faces_for_sequence:
                    continue

                while len(faces_for_sequence) < SEQUENCE_LENGTH:
                    faces_for_sequence.append(faces_for_sequence[-1])

                sequence_tensor = torch.stack(faces_for_sequence[:SEQUENCE_LENGTH]).unsqueeze(0).to(device)
                logits = model(sequence_tensor)
                proba = float(torch.sigmoid(logits).flatten()[0].item())
                confidences.append(proba)
                valid_sequences += 1

                if proba > 0.5:
                    fake_votes += 1
                else:
                    real_votes += 1

        if valid_sequences == 0:
            return {"error": "Aucun visage détecté dans la vidéo."}

        final_status = "Fake" if fake_votes > real_votes else "Real"
        avg_fake_score = float(sum(confidences) / len(confidences))
        confidence_score = avg_fake_score if final_status == "Fake" else 1.0 - avg_fake_score

        return {
            "status": final_status,
            "confidence_score": round(confidence_score, 4),
            "fake_score": round(avg_fake_score, 4),
            "sequences_analyzed": valid_sequences,
            "votes": {"fake": fake_votes, "real": real_votes},
        }
    except Exception as exc:
        return {"error": f"Erreur analyse deepfake: {exc!s}"}
    finally:
        if cap is not None:
            cap.release()