@echo off
:: ══════════════════════════════════════════════════════
::  AirQual CM — Lancement Backend FastAPI AlphaInfera
:: ══════════════════════════════════════════════════════

cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   AirQual CM — Backend AlphaInfera       ║
echo  ║   IndabaX Cameroon 2026                  ║
echo  ╚══════════════════════════════════════════╝
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python non trouve. Installe Python 3.9+ depuis python.org
    pause
    exit /b 1
)

if not exist "models\best_model_rf.joblib" (
    echo.
    echo [ERREUR] models\best_model_rf.joblib introuvable !
    echo.
    echo  Exécute la cellule d'export dans ton notebook Colab,
    echo  puis copie les 7 fichiers dans le dossier models\
    echo.
    pause
    exit /b 1
)

echo [OK] Modele RF trouve
echo [OK] Installation dependances...
pip install -r requirements.txt -q

echo.
echo [START] Serveur sur http://0.0.0.0:8000
echo         Documentation : http://localhost:8000/docs
echo         Pour Flutter (emulateur) : http://10.0.2.2:8000
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
