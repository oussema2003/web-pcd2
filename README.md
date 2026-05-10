[README.md](https://github.com/user-attachments/files/27574982/README.md)
# 🤖 HireBot — Plateforme de Recrutement Intelligente assistée par IA

<div align="center">

![HireBot](https://img.shields.io/badge/HireBot-Recrutement%20IA-blue?style=for-the-badge&logo=robot)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2.7-092E20?style=for-the-badge&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0.1-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![MariaDB](https://img.shields.io/badge/MariaDB-003545?style=for-the-badge&logo=mariadb&logoColor=white)

**Université de la Manouba — École Nationale des Sciences de l'Informatique**  
*Projet PCD/26/67 — Année universitaire 2025/2026*

</div>

---

## 📖 Description

**HireBot** est une plateforme de recrutement intelligente qui combine la **vision par ordinateur**, le **traitement automatique du langage naturel (NLP)** et l'**analyse émotionnelle vocale** pour assister les responsables RH dans l'évaluation des candidatures vidéo.

Face à l'essor des contenus synthétiques générés par IA (deepfakes), HireBot propose une chaîne d'analyse complète :

1. **Détection de deepfakes** — vérification de l'authenticité de la vidéo du candidat
2. **Transcription et analyse sémantique** — évaluation de la pertinence du discours par rapport au poste
3. **Analyse émotionnelle vocale** — estimation du stress via Wav2Vec 2.0
4. **Score de correspondance** — aide à la décision pour le recruteur

---

## 👥 Auteurs

| Nom | Rôle |
|---|---|
| **Oussema HIDOURI** | Développeur principal / Chef de projet |
**Encadrant :** Dr. Majdi JRIBI
---

## 🏗️ Architecture du Projet

```
web-pcd2/
├── frontend/               # Application React (TypeScript + Vite)
│   └── src/
│       ├── components/     # Composants réutilisables (Navbar, ChatWidget, Dashboard...)
│       ├── pages/          # Pages principales (Auth, Dashboard, Offres...)
│       ├── hooks/          # Hooks React (useAuth...)
│       └── api/            # Client Axios vers l'API Django
│
├── backend/                # API REST Django
│   ├── accounts/           # Authentification, rôles, profils utilisateurs
│   ├── jobs/               # Offres d'emploi, candidatures, analyse IA
│   ├── chat/               # Chatbot via Ollama
│   └── core/
│       ├── settings.py     # Configuration globale Django
│       └── ml/             # Services de détection deepfake & analyse audio
│
└── code du model/          # Notebooks Jupyter — entraînement du modèle deepfake
```

### Stack Technologique

| Couche | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, shadcn/ui, Axios |
| **Backend** | Django 4.2.7, Django REST Framework, JWT |
| **Base de données** | MariaDB |
| **IA / Deepfake** | PyTorch 2.0, XceptionNet, EfficientNet-B4, Transformer Encoder |
| **Détection visage** | MTCNN |
| **Transcription** | AssemblyAI (Speech-to-Text) |
| **Analyse émotionnelle** | Wav2Vec 2.0 (audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim) |
| **Score sémantique** | Groq API |
| **Chatbot** | Ollama (qwen2.5:latest) |

---

## 🧠 Modèle de Détection de Deepfakes

Le modèle combine deux niveaux d'analyse :

### Architecture CNN + Transformer
- **Extraction spatiale (par frame)** :
  - `XceptionNet` → vecteur 2048 dimensions
  - `EfficientNet-B4` → vecteur 1792 dimensions
  - Concaténation + projection linéaire vers 512 dimensions (GELU + LayerNorm + Dropout)
- **Modélisation temporelle** :
  - Transformer Encoder (3 couches, 8 têtes d'attention, dropout=0.5)
  - Mean Pooling → tête MLP → logit binaire (Real / Fake)

### Données d'entraînement
- Dataset : **DFDC** (DeepFake Detection Challenge — Meta)
- 38 000 vidéos équilibrées (REAL / FAKE)
- Jusqu'à 15 frames par vidéo, visages extraits via MTCNN (224×224)
- Split : 68% train / 12% validation / 20% test

### Performances sur le jeu de test (44 899 échantillons)

| Métrique | Valeur |
|---|---|
| **Accuracy** | **95.18%** |
| Précision (Fake) | 96.19% |
| Rappel (Fake) | 94.10% |
| F1-Score (Fake) | 95.13% |
| **AUC-ROC** | **0.9905** |
| AUC-PR | 0.9909 |

---

## 🚀 Installation & Lancement

### Prérequis

- Python 3.10+
- Node.js 18+
- MariaDB
- [Ollama](https://ollama.com/) (pour le chatbot)
- GPU recommandé (CUDA) pour l'inférence deepfake

---

### 1. Cloner le dépôt

```bash
git clone https://github.com/oussema2003/web-pcd2.git
cd web-pcd2
```

---

### 2. Backend Django

```bash
cd backend

# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer la base de données dans core/settings.py
# (host, port, nom de la base, utilisateur, mot de passe MariaDB)

# Appliquer les migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

Le backend sera disponible sur `http://localhost:8000/api/`

---

### 3. Frontend React

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer en développement
npm run dev
```

Le frontend sera disponible sur `http://localhost:5173`

---

### 4. Chatbot Ollama

```bash
# Installer Ollama : https://ollama.com/download

# Télécharger le modèle
ollama pull qwen2.5:latest

# Lancer Ollama (port 11434 par défaut)
ollama serve
```

---

### 5. Variables d'environnement (optionnel)

Créer un fichier `.env` dans `backend/` :

```env
SECRET_KEY=your_django_secret_key
DEBUG=True

DB_NAME=hirebot_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

ASSEMBLYAI_API_KEY=your_assemblyai_key
GROQ_API_KEY=your_groq_key
```

---

## 📡 Principaux Endpoints API

| Endpoint | Méthode | Description |
|---|---|---|
| `/api/auth/login/` | POST | Connexion — retourne tokens JWT |
| `/api/auth/me/` | GET | Profil de l'utilisateur connecté |
| `/api/offres/` | GET / POST | Lister ou créer des offres d'emploi |
| `/api/candidatures/<id>/analyse-ia/` | POST | Analyse CV + transcription → score Groq |
| `/api/candidatures/<id>/analyse-audio/` | POST | Transcription + détection stress Wav2Vec2 |
| `/api/chat/` | POST | Message → réponse chatbot Ollama |
| `/api/check-video-deepfake/` | POST | Détection deepfake sur vidéo MP4 |

---

## 🎯 Fonctionnalités Principales

### Pour le Candidat
- Consulter les offres d'emploi publiées
- Soumettre une candidature (CV PDF/DOC + vidéo MP4)
- Assistance via le chatbot intégré

### Pour le Recruteur (RH)
- Tableau de bord interactif
- Créer, modifier et supprimer des offres
- Consulter les candidatures avec résultats IA :
  - Résultat deepfake (Authentique / Généré par IA)
  - Score de correspondance (0–100)
  - Analyse émotionnelle (Arousal, Valence, Dominance)
  - Transcription de la vidéo
- Accepter ou refuser les candidatures

### Pour l'Administrateur
- Gestion globale des utilisateurs et de leurs rôles
- Supervision de toutes les candidatures
- Consultation des résultats de tous les modules IA

---

## 📊 Pipeline de Traitement d'une Candidature

```
Candidat soumet (CV + Vidéo)
        ↓
[1] Détection deepfake (CNN + Transformer)
        ↓
   Vidéo IA détectée ? ──→ OUI → Candidature rejetée automatiquement
        ↓ NON
[2] Extraction audio (OpenCV)
        ↓
[3] Transcription Speech-to-Text (AssemblyAI)
        ↓
[4] Analyse émotionnelle (Wav2Vec 2.0)
        ↓
[5] Score de correspondance CV + transcription vs offre (Groq)
        ↓
Résultats disponibles pour le Recruteur
```

---

## 🧪 Entraînement du Modèle

Les notebooks d'entraînement sont dans `code du model/`.

Bibliothèques requises :

```bash
pip install torch torchvision timm facenet-pytorch opencv-python scikit-learn tqdm
```

Paramètres clés de l'entraînement :

| Paramètre | Valeur |
|---|---|
| Optimiseur | AdamW (lr=1e-4, weight_decay=1e-2) |
| Scheduler | Warmup 2 époques + Cosine Annealing |
| Époques | 20 |
| Batch size | 32 |
| Séquence temporelle | 4 frames, stride 2 |
| Freeze ratio backbones | 0.7 |
| Early stopping patience | 7 |

---

## 🛠️ Dépannage

Consultez le fichier [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) pour les problèmes courants (erreurs MTCNN, connexion MariaDB, CORS, Ollama, etc.).

---

## 📚 Technologies & Références Clés

- [PyTorch](https://pytorch.org/) — Framework deep learning
- [timm](https://github.com/huggingface/pytorch-image-models) — Modèles pré-entraînés (XceptionNet, EfficientNet)
- [MTCNN](https://github.com/ipazc/mtcnn) — Détection et alignement facial
- [AssemblyAI](https://www.assemblyai.com/) — Speech-to-Text
- [Groq](https://groq.com/) — Analyse sémantique et scoring
- [Hugging Face — Wav2Vec2](https://huggingface.co/audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim) — Analyse émotionnelle
- [Ollama](https://ollama.com/) — Chatbot LLM local (qwen2.5)
- [DFDC Dataset](https://www.kaggle.com/competitions/deepfake-detection-challenge) — Données d'entraînement

---

## 📄 Licence

Ce projet a été réalisé dans le cadre académique à l'ENSI (École Nationale des Sciences de l'Informatique), Université de la Manouba, Tunisie.

---

<div align="center">
<i>HireBot — Rendre le recrutement plus intelligent, plus sûr et plus équitable.</i>
</div>
