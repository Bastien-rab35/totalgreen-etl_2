# SQL Scripts - MSPR TotalGreen ETL

Ce dossier contient les scripts SQL pour le projet TotalGreen ETL.

## 📊 Scripts principaux (Modèle en Étoile)

### Création et Migration
- **`star_schema.sql`** - Schéma complet du modèle en étoile (Data Warehouse)
  - 4 tables de dimensions : `dim_time`, `dim_city`, `dim_weather_condition`, `dim_air_quality_level`
  - 1 table de faits : `fact_measures`
  - Fonctions utilitaires : `populate_dim_time()`, `get_aqi_level_id()`
  
- **`migrate_to_star_schema.sql`** - Migration des données depuis le modèle normalisé
  - Remplissage des dimensions
  - Migration zéro-perte vers `fact_measures`
  - Vérifications post-migration

### Analyses
- **`queries_olap.sql`** - 20+ requêtes d'analyses multidimensionnelles
  - Analyses temporelles (tendances, patterns)
  - Analyses géographiques (classements villes)
  - Analyses par condition météo
  - Analyses qualité de l'air par niveau AQI
  - Cubes OLAP et corrélations

### Maintenance
- **`cleanup_old_tables.sql`** - Nettoyage des tables obsolètes
  - Supprime `measures` (remplacée par `fact_measures`)
  - Supprime `cities` (remplacée par `dim_city`)
  - Vérifications de sécurité avant suppression

## 🗄️ Ancien modèle (Archive)

- **`schema.sql`** - Schéma du modèle normalisé (ancien)
- **`archive/`** - Anciens scripts d'analyse et d'insertion

## 📖 Ordre d'exécution (Déploiement)

Pour déployer le Data Warehouse depuis zéro :

```sql
-- 1. Créer le schéma en étoile
\i star_schema.sql

-- 2. Migrer les données existantes
\i migrate_to_star_schema.sql

-- 3. (Optionnel) Nettoyer les anciennes tables
\i cleanup_old_tables.sql

-- 4. Tester avec les requêtes OLAP
\i queries_olap.sql
```

## 🔗 Liens

- Modèle normalisé → Modèle en étoile : Migration complétée le 2026-02-09
- Documentation complète : voir `/docs/DATA_LAKE_ARCHITECTURE.md`
