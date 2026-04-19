"""
Analyse vocale (arousal, dominance, valence) via wav2vec2 MSP-DIM.
Le modèle est chargé une seule fois (lazy singleton) pour éviter de recharger à chaque requête.
"""

from __future__ import annotations

_processor = None
_model = None


def _get_model():
    global _processor, _model
    if _model is None:
        import warnings

        import torch
        from transformers import AutoModelForAudioClassification, AutoProcessor
        from transformers.utils import logging as hf_logging

        hf_logging.set_verbosity_error()
        warnings.filterwarnings(
            "ignore",
            message=".*Some weights of.*were not initialized from the model checkpoint.*",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=".*You should probably TRAIN this model on a down-stream task.*",
            category=UserWarning,
        )

        model_name = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"
        _processor = AutoProcessor.from_pretrained(model_name)
        _model = AutoModelForAudioClassification.from_pretrained(model_name)
        _model.eval()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = _model.to(device)
    return _processor, _model


def analyser_stress(chemin_mp3: str) -> dict:
    import librosa
    import torch

    processor, model = _get_model()
    device = next(model.parameters()).device

    audio_array, _ = librosa.load(chemin_mp3, sr=16000)
    inputs = processor(audio_array, sampling_rate=16000, return_tensors="pt")
    inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    scores = outputs.logits[0].tolist()
    arousal, dominance, valence = scores[0], scores[1], scores[2]

    etat = "Calme"
    if arousal > 0.6 and valence < 0.5:
        etat = "Stress fort"
    elif arousal > 0.5:
        etat = "Légèrement nerveux"

    return {
        "arousal": float(arousal),
        "dominance": float(dominance),
        "valence": float(valence),
        "etat": etat,
    }
