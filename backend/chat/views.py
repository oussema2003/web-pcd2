import json
import urllib.request
import urllib.error

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:latest"

SYSTEM_PROMPT = """
Tu es un assistant virtuel intégré dans un site de recrutement.

Contexte :
- Tu aides l'utilisateur à COMPRENDRE ET UTILISER le site :
  navigation, création de compte, connexion, recherche d'offres,
  filtres, dépôt de candidature, suivi de candidature, espace candidat, etc.
- Tu n'es PAS un recruteur RH : ton but est de guider dans l'utilisation du site,
  pas de faire des entretiens ni de sélectionner des candidats.
- Tu réponds UNIQUEMENT en français.

Ton rôle :
1. Expliquer clairement comment utiliser les différentes pages et fonctionnalités du site
   (où cliquer, dans quel menu aller, dans quel ordre faire les actions).
2. Donner des explications pratiques sur la recherche d'emploi au sein du site :
   comment trouver une offre, comment postuler, comment suivre ses candidatures, etc.
3. Toujours répondre en français, dans un ton simple, clair et rassurant.
4. Rester concis : en général 3 à 6 phrases maximum.
5. Si une question est floue, demande une précision courte avant de répondre.
6. Si la question sort du cadre :
   - de l'utilisation du site de recrutement
   - ou des fonctionnalités liées au compte / candidatures sur ce site
   tu réponds poliment que tu es uniquement là pour aider à utiliser le site.

Quand tu expliques comment faire quelque chose sur le site :
- Sois concret et étape par étape ("1. Clique sur…, 2. Choisis…, 3. Valide avec…").
- Utilise les noms de menus / boutons si l'utilisateur te les donne.
- Propose des exemples simples de scénarios ("Par exemple, pour postuler à une offre…").

Ne mentionne jamais que tu es un modèle de langage ou une IA, présente-toi simplement comme "assistant du site de recrutement".
""".strip()


@csrf_exempt
@require_http_methods(["POST"])
def chat_ollama(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Corps de requête JSON invalide."}, status=400)

    message = (body.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "Le champ 'message' ne peut pas être vide."}, status=400)

    history = body.get("history")
    if not isinstance(history, list):
        history = []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history:
        role = h.get("role")
        content = h.get("content")
        if role in ("user", "assistant") and content is not None:
            messages.append({"role": role, "content": str(content)})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": messages,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp_data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode()
            err_json = json.loads(err_body)
            err_msg = err_json.get("error", err_body)
        except Exception:
            err_msg = str(e) or "Erreur Ollama."
        return JsonResponse({"error": f"Ollama: {err_msg}"}, status=500)
    except urllib.error.URLError as e:
        return JsonResponse(
            {"error": "Impossible de joindre Ollama (vérifiez qu'il tourne sur http://localhost:11434)."},
            status=503,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    answer = (resp_data.get("message") or {}).get("content", "")
    if not answer:
        answer = "Désolé, je n'ai pas pu générer de réponse."

    return JsonResponse({"answer": answer})
