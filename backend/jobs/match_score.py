"""
Score de correspondance offre / candidature à partir de la description du poste
et du texte candidat (transcription + éventuellement réponses formulaire selon l’appelant).
L’endpoint analyse-ia n’envoie que la transcription vidéo (.txt) à Groq.
Peut s'appuyer sur Groq (JSON strict) lorsque GROQ_API_KEY est configurée.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

_MAX_CONTEXT_CHARS = 24_000


def _words(text: str) -> set[str]:
    return set(re.findall(r"[\wàâäéèêëïîôùûç'-]+", text.lower(), flags=re.UNICODE))


def build_candidate_text(
    transcription: str | None,
    answers: dict[str, Any] | None,
) -> str:
    parts: list[str] = []
    if transcription and transcription.strip():
        parts.append(transcription.strip())
    if answers:
        for v in answers.values():
            if isinstance(v, str) and v.strip():
                parts.append(v.strip())
    return " ".join(parts)


def clean_llm_json_string(raw: str) -> str:
    """Retire les blocs Markdown ```json ... ``` et isole l'objet JSON principal."""
    text = (raw or "").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return text.strip()


def validate_match_payload(data: Any) -> dict[str, int | str]:
    """
    Valide l'objet déjà parsé : {"score": nombre, "justification": str}.
    Lève ValueError ou TypeError si la forme est incorrecte.
    """
    if not isinstance(data, dict):
        raise ValueError("La réponse n'est pas un objet JSON.")
    if "score" not in data or "justification" not in data:
        raise ValueError("Champs 'score' ou 'justification' manquants.")
    raw_score = data["score"]
    if isinstance(raw_score, bool):
        raise ValueError("Score booléen invalide.")
    score = int(round(float(raw_score)))
    justification = str(data["justification"]).strip()
    if not justification:
        raise ValueError("Justification vide.")
    if score < 1 or score > 100:
        raise ValueError("Score hors plage 1–100.")
    return {"score": score, "justification": justification}


def groq_match_raw_response(
    description_offre: str,
    contenu_fichier_candidat: str,
    api_key: str,
    model_name: str = "llama-3.3-70b-versatile",
) -> str:
    """Appelle l'API Groq (chat completions) et renvoie le texte brut du modèle (JSON attendu)."""
    from groq import BadRequestError, Groq

    desc = (description_offre or "").strip()[:_MAX_CONTEXT_CHARS]
    cand = (contenu_fichier_candidat or "").strip()[:_MAX_CONTEXT_CHARS]

    system_instruction = (
        "Tu es un expert RH. Tu compares UNIQUEMENT la section « transcription_vidéo_candidat » (contenu réel du fichier .txt "
        "de la vidéo) avec « description_offre ». N’invente pas de contenu candidat : tout ce que tu cites doit exister dans la transcription.\n"
        "Réponds STRICTEMENT par un seul objet JSON valide, sans markdown, format exact :\n"
        '{"score": <entier>, "justification": "<une phrase en français>"}\n'
        "Règle obligatoire pour justification : elle DOIT commencer par un extrait LITTÉRAL court entre guillemets français « … » "
        "(2 à 15 mots) COPIÉS depuis transcription_vidéo_candidat, puis une virgule et ton analyse par rapport à l’offre. "
        "Si la transcription ne contient pas assez de mots, cite ce qui est possible.\n"
        "Score sur 100 (ENTIER 1–100), pourcentage d’adéquation, pas une note sur 10. "
        "Grille : 81–100 très forte ; 61–80 bonne ; 41–60 partielle ; 22–40 liens faibles ; 12–21 très limité ; 1–11 quasi aucun lien."
    )

    if not cand:
        user_message = (
            f"description_offre:\n{desc}\n\n"
            "transcription_vidéo: (vide — aucun texte issu de la vidéo)\n\n"
            "Comme il n'y a rien à comparer à la description du poste, attribue un score entre 1 et 15 et une justification qui le dit clairement."
        )
    else:
        n_chars = len(cand)
        user_message = (
            f"description_offre :\n{desc}\n\n"
            f"---\ntranscription_vidéo_candidat (copie intégrale, {n_chars} caractères) :\n{cand}\n---\n\n"
            "Lis toute la transcription ci-dessus. Ton score et ta justification doivent découler de ce texte et de la description du poste."
        )

    client = Groq(api_key=api_key)
    common = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.28,
        "top_p": 0.85,
        "max_tokens": 320,
    }
    try:
        completion = client.chat.completions.create(
            **common,
            response_format={"type": "json_object"},
        )
    except BadRequestError:
        completion = client.chat.completions.create(**common)
    choice = completion.choices[0].message
    text = (getattr(choice, "content", None) or "").strip()
    if not text:
        raise ValueError("Réponse Groq sans texte exploitable.")
    return text


def compute_correspondance(
    offre_description: str,
    transcription: str | None,
    answers: dict[str, Any] | None,
) -> dict[str, int | str]:
    candidate_text = build_candidate_text(transcription, answers)

    if not candidate_text.strip():
        if answers is None:
            just_empty = (
                "Aucune transcription vidéo n'est disponible pour estimer la correspondance au poste."
            )
        else:
            just_empty = (
                "Aucune transcription ni réponse textuelle n'est disponible pour estimer "
                "la correspondance au poste."
            )
        return {"score": 0, "justification": just_empty}

    job = (offre_description or "").strip()
    if not job:
        return {
            "score": int(min(100, max(0, len(candidate_text) // 50))),
            "justification": "La description du poste est vide ; le score est indicatif uniquement.",
        }

    seq = SequenceMatcher(None, job.lower(), candidate_text.lower()).ratio()
    wj, wc = _words(job), _words(candidate_text)
    union = wj | wc
    jaccard = (len(wj & wc) / len(union)) if union else 0.0
    # Mots un peu plus longs : mieux aligné sur « compétences / outils » qu’un Jaccard sur tout le JD.
    long_overlap = {w for w in (wj & wc) if len(w) >= 4}
    overlap_signal = min(1.0, len(long_overlap) / 12.0)
    combined = 0.42 * seq + 0.33 * jaccard + 0.25 * overlap_signal
    score = int(round(max(0, min(100, combined * 100))))

    if score >= 75:
        justification = (
            "Le contenu de la candidature présente une forte proximité avec la description du poste "
            "(mots-clés et formulation)."
        )
    elif score >= 50:
        justification = (
            "Adéquation modérée : plusieurs éléments de la candidature recoupent les exigences de l'offre."
        )
    elif score >= 25:
        justification = (
            "Correspondance partielle : le profil exprimé ne couvre qu'une partie des attentes du rôle."
        )
    else:
        justification = (
            "Faible recouvrement entre les informations fournies par le candidat et le descriptif du poste."
        )

    return {"score": score, "justification": justification}
