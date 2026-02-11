## Backend Django (API)

### Installation

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # optionnel
python manage.py runserver 8000
```

### Endpoints principaux

- **Auth**
  - `POST /api/auth/register/` – inscription `{ email, username, password, role }`
  - `POST /api/auth/login/` – connexion, renvoie `{ access, refresh, user }`
  - `GET  /api/auth/me/` – infos du user connecté (authentifié)
  - `POST /api/auth/logout/` – déconnexion logique (le frontend supprime les tokens)
  - `POST /api/auth/token/refresh/` – rafraîchir le token d'accès `{ refresh: "token" }` → `{ access: "new_token" }`
  - `POST /api/auth/token/blacklist/` – mettre en blacklist un refresh token `{ refresh: "token" }`
  - `GET  /api/auth/candidates/` – liste de tous les candidats (RH uniquement)

- **Offres**
  - `GET  /api/offres/` – liste publique des offres
  - `GET  /api/offres/<id>/` – détail d’une offre (+ champ `has_applied` si connecté)
  - `GET  /api/offres/mine/` – offres créées par le recruteur connecté (RH)
  - `POST /api/offres/mine/` – créer une offre (RH)
  - `PUT  /api/offres/<id>/` – modifier une offre (RH propriétaire)
  - `DELETE /api/offres/<id>/` – supprimer une offre (RH propriétaire)

- **Candidatures**
  - `POST /api/offres/<id>/postuler/` – postuler à une offre (candidat)
  - `GET  /api/candidatures/me/` – candidatures du candidat connecté
  - `GET  /api/offres/<id>/candidatures/` – candidatures pour une offre (RH propriétaire)
  - `PATCH /api/candidatures/<id>/` – changer le statut d’une candidature (RH propriétaire)

