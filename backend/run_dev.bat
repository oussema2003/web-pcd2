@echo off
REM Démarre Django avec un venv local (.venv) pour éviter les conflits d'interpréteur (ex. librosa manquant).
REM Score IA (Groq) : cle dans backend\.env (GROQ_API_KEY) ou variable d'environnement Windows.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creation du venv .venv...
  py -3 -m venv .venv
  if errorlevel 1 (
    python -m venv .venv
  )
)

echo Installation / mise a jour des dependances...
".venv\Scripts\python.exe" -m pip install -q --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo Demarrage du serveur sur ce Python : 
".venv\Scripts\python.exe" -c "import sys; print(sys.executable)"

".venv\Scripts\python.exe" manage.py runserver %*
