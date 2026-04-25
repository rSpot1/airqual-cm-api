#!/bin/bash
# ══════════════════════════════════════════════════════
#  AirQual CM — Lancement Backend FastAPI AlphaInfera
# ══════════════════════════════════════════════════════

set -e

BACKEND_DIR="$(dirname "$0")"
cd "$BACKEND_DIR"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   AirQual CM — Backend AlphaInfera       ║"
echo "║   IndabaX Cameroon 2026                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trouvé. Installe Python 3.9+ depuis python.org"
    exit 1
fi
echo "✓ Python: $(python3 --version)"

# Vérifier le dossier models/
if [ ! -f "models/best_model_rf.joblib" ]; then
    echo ""
    echo "❌  ERREUR : models/best_model_rf.joblib introuvable !"
    echo ""
    echo "   → Exécute la cellule d'export dans ton notebook Colab,"
    echo "     puis copie les 7 fichiers dans le dossier models/"
    echo ""
    echo "   Fichiers attendus :"
    echo "     models/best_model_rf.joblib"
    echo "     models/features.json"
    echo "     models/label_encoder_region.joblib"
    echo "     models/city_profiles.csv"
    echo "     models/risk_table.csv"
    echo "     models/global_stats.json"
    echo "     models/city_enc_map.json"
    echo ""
    exit 1
fi
echo "✓ Modèle RF trouvé"

# Installer les dépendances si besoin
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "📦 Installation des dépendances..."
    pip install -r requirements.txt -q
fi
echo "✓ Dépendances OK"

echo ""
echo "🚀 Démarrage du serveur sur http://0.0.0.0:8000"
echo "   → Documentation : http://localhost:8000/docs"
echo "   → Pour Flutter (émulateur Android) : http://10.0.2.2:8000"
echo ""
echo "   Ctrl+C pour arrêter"
echo ""

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
