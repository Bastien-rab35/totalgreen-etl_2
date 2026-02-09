# Documentation Technique - TotalGreen ETL

Documentation complète du projet de surveillance environnementale.

---

## 📚 Documents Principaux

### [ARCHITECTURE.md](ARCHITECTURE.md)
Architecture technique complète du système :
- Modèle en étoile (Star Schema)
- Pipeline ETL 3 couches
- Data Lake et Data Warehouse
- Stratégies de transformation
- Technologies utilisées

### [SECURITE.md](SECURITE.md)
Sécurité et conformité RGPD :
- Hébergement UE et souveraineté des données
- Gestion des secrets et authentification
- Contrôle d'accès et RLS
- Conservation et purge des données

---

## 🗂️ Documents Archivés

Documents techniques de développement et diagnostics (conservés pour historique) :

- `archive/AUDIT_COMPLET.md` - Audit complet du système
- `archive/AUDIT_PHASE1.md` - Audit phase 1
- `archive/CORRECTION_TIMESTAMPS.md` - Corrections timestamps
- `archive/DIAGNOSTIC_GITHUB_ACTIONS.md` - Debug GitHub Actions
- `archive/STRATEGIE_FUSION.md` - Stratégie fusion météo+AQI
- `archive/DATA_LAKE_ARCHITECTURE.md` - Ancienne architecture data lake

---

## 🚀 Démarrage Rapide

### Installation
```bash
# Cloner le projet
git clone https://github.com/Bastien-rab35/totalgreen-etl.git
cd totalgreen-etl

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Configurer .env
cp .env.example .env
# Éditer .env avec vos clés API
```

### Configuration Base de Données
```bash
# Exécuter dans Supabase SQL Editor:
# 1. Créer le schéma
sql/star_schema.sql

# 2. (Si migration) Migrer les données
sql/migrate_to_star_schema.sql

# 3. (Optionnel) Nettoyer anciennes tables
sql/cleanup_old_tables.sql
```

### Exécution
```bash
# Collecte (Extract → Data Lake)
python src/etl_extract_to_lake.py

# Transformation (Data Lake → Data Warehouse)
python src/etl_transform_to_db.py

# Vérification
python scripts/verify_star_schema.py
```

---

## 📊 Structure du Projet

```
MSPR 1/
├── docs/                    # Documentation (ici)
│   ├── ARCHITECTURE.md
│   ├── SECURITE.md
│   └── archive/            # Docs historiques
├── sql/                    # Scripts SQL
│   ├── star_schema.sql
│   ├── migrate_to_star_schema.sql
│   └── queries_olap.sql
├── src/                    # Code source Python
│   ├── services/          # Services modulaires
│   ├── etl_extract_to_lake.py
│   └── etl_transform_to_db.py
├── scripts/               # Scripts utilitaires
├── data/                  # Données référence
└── .github/workflows/     # Automatisation
```

---

## 🔗 Liens Utiles

- **Dépôt GitHub** : https://github.com/Bastien-rab35/totalgreen-etl
- **Supabase Dashboard** : https://supabase.com/dashboard
- **OpenWeather API** : https://openweathermap.org/api
- **AQICN API** : https://aqicn.org/api/

---

## 📝 Changelog

### Version 2.0 (2026-02-09)
- ✨ Implémentation Data Warehouse en étoile
- 🔄 Pipeline ETL mis à jour (insertion directe fact_measures)
- 📊 20+ requêtes OLAP
- 🧹 Nettoyage et organisation projet

### Version 1.0 (2024-01-12)
- 🎉 Version initiale avec modèle normalisé
- ⚙️ Pipeline ETL double (extract + transform)
- 🌍 Data Lake JSONB
- 🔐 Conformité RGPD

---

**Projet** : TotalGreen ETL - Surveillance Environnementale  
**Auteur** : Bastien Rabane  
**Dernière mise à jour** : 2026-02-09
