# Scripts Utilitaires - MSPR TotalGreen ETL

Scripts Python pour la maintenance et la vérification du projet.

## 🔧 Scripts actifs

### Vérification
- **`check_bdd_status.py`** - Vérifie l'état de la base de données
- **`check_data_lake.py`** - Vérifie l'état du data lake
- **`check_fusion_strategy.py`** - Vérifie la stratégie de fusion météo+AQI
- **`verify_star_schema.py`** - Vérifie le déploiement du modèle en étoile

### Maintenance
- **`reset_and_reload.py`** - Reset complet et rechargement des données

## 📦 Archive

Scripts de déploiement temporaires (déjà exécutés) :
- `archive/deploy_star_schema.py`
- `archive/deploy_star_schema_postgres.py`

## 📖 Utilisation

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier le modèle en étoile
python scripts/verify_star_schema.py

# Vérifier l'état du data lake
python scripts/check_data_lake.py

# Vérifier l'état de la BDD
python scripts/check_bdd_status.py
```
