# Guide de dépannage - Erreur "Failed to fetch"

## Problème
L'erreur "Failed to fetch" apparaît lors de la création de compte ou de la connexion.

## Solutions

### 1. Vérifier que le backend Django est démarré

**Ouvrir un terminal et exécuter :**

```bash
cd backend
python manage.py runserver
```

Vous devriez voir :
```
Starting development server at http://127.0.0.1:8000/
```

### 2. Vérifier que le backend répond

Ouvrir dans votre navigateur :
- `http://127.0.0.1:8000/` → Devrait afficher "Talent Connect API is running..."
- `http://127.0.0.1:8000/admin/` → Devrait afficher la page d'administration Django

### 3. Vérifier l'URL de l'API dans le frontend

Le fichier `frontend/.env` doit contenir :
```
VITE_API_URL=http://localhost:8000/api
```

### 4. Redémarrer le serveur frontend après modification de .env

Si vous avez modifié `.env`, redémarrer le serveur frontend :
```bash
cd frontend
npm run dev
```

### 5. Vérifier les ports

- **Backend** : doit tourner sur le port **8000** (http://localhost:8000)
- **Frontend** : peut tourner sur n'importe quel port (généralement 5173 pour Vite)

### 6. Vérifier CORS

La configuration CORS a été mise à jour pour permettre toutes les origines en mode développement. Si le problème persiste :

1. Vérifier que `DEBUG = True` dans `backend/core/settings.py`
2. Redémarrer le serveur Django après modification

### 7. Tester l'API directement

Vous pouvez tester l'API avec curl ou Postman :

**Test de connexion :**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

**Test d'inscription :**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123","role":"candidate"}'
```

## Checklist rapide

- [ ] Backend Django démarré sur http://localhost:8000
- [ ] Frontend démarré (généralement sur http://localhost:5173)
- [ ] Fichier `.env` dans `frontend/` avec `VITE_API_URL=http://localhost:8000/api`
- [ ] Pas de firewall bloquant les connexions
- [ ] Console du navigateur ouverte pour voir les erreurs détaillées

## Messages d'erreur améliorés

Les messages d'erreur ont été améliorés pour indiquer clairement si le problème vient de :
- La connexion au serveur backend
- Des identifiants invalides
- D'autres erreurs
