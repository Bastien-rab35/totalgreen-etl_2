# SQL Scripts - MSPR TotalGreen ETL

Ce dossier contient les scripts SQL pour le projet TotalGreen ETL.

## Scripts principaux (Modèle en Étoile)

### Création et Migration
- **`star_schema.sql`** - Schéma complet du modèle en étoile (Data Warehouse)
  - 4 tables de dimensions : `dim_time`, `dim_city`, `dim_weather_condition`, `dim_air_quality_level`
  - 1 table de faits : `fact_measures`
  - Fonctions utilitaires : `populate_dim_time()`, `get_aqi_level_id()`

- **`create_dim_date.sql`** - Création de la dimension temporelle
  - Remplace dim_time par dim_date
  - ~1460 jours (2024-2027)
  
- **`update_cities_aqi_stations.sql`** - Configuration des stations AQI spécifiques
  - Stations optimisées pour Lyon et Lille
  - Amélioration qualité des données

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

## Ancien modèle (Archive)

- **`schema.sql`** - Schéma du modèle normalisé (ancien)
- **`archive/`** - Anciens scripts d'analyse et d'insertion

## Ordre d'exécution (Déploiement)

Pour déployer le Data Warehouse depuis zéro :

```sql
-- 1. Créer le schéma en étoile
\i star_schema.sql

-- 2. Créer la dimension temporelle
\i create_dim_date.sql

-- 3. Configurer les stations AQI
\i update_cities_aqi_stations.sql

-- 4. Tester avec les requêtes OLAP
\i queries_olap.sql
```

## Liens

- Modèle normalisé → Modèle en étoile : Migration complétée le 2026-02-09
- Documentation complète : voir `docs/ARCHITECTURE.md`
