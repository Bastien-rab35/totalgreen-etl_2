#!/bin/bash
# Guide de démarrage GoodAir - MSPR 2

set -e  # Arrêter en cas d'erreur

echo "🚀 GoodAir - Initialisation de l'environnement"
echo "=============================================="

# Vérifier que .env existe
if [ ! -f ".env" ]; then
    echo "❌ Erreur: Fichier .env introuvable"
    echo "   Créez un fichier .env avec les variables d'environnement:"
    echo "   - OPENWEATHER_API_KEY"
    echo "   - AQICN_API_KEY"
    echo "   - TOMTOM_API_KEY"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
    exit 1
fi

# Activer l'environnement virtuel
if [ ! -d ".venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv .venv
fi

echo "✓ Activation de l'environnement virtuel"
source .venv/bin/activate

# Installer les dépendances
echo "📚 Installation des dépendances..."
pip install -q -r requirements.txt

echo ""
echo "✅ Environnement prêt!"
echo ""
echo "Commandes disponibles:"
echo "====================="
echo ""
echo "1️⃣  EXTRACTION (Data Lake)"
echo "    python src/etl_extract_to_lake.py"
echo ""
echo "2️⃣  TRANSFORMATION (Data Warehouse)"
echo "    python src/etl_transform_to_db.py"
echo ""
echo "3️⃣  VALIDATION (Qualité données)"
echo "    python scripts/validate_data_quality.py --hours 24"
echo ""
echo "4️⃣  DASHBOARD STREAMLIT (Visualisation interactive)"
echo "    streamlit run app/dashboard.py"
echo ""
echo "5️⃣  NOTEBOOKS (Analyses statistiques)"
echo "    jupyter notebook notebooks/02_statistical_models.ipynb"
echo ""
echo "=============================================="
echo "Pour plus d'infos: cat README.md"
