# Historique des modifications - TotalGreen ETL

Ce document retrace les principales évolutions techniques du projet.

---

## Version 2.1 - Import données historiques (Mars 2026)

### Import CSV AQICN
- Import de 1,567 enregistrements historiques depuis `waqi-covid19-airqualitydata-2026.csv`
- Lyon: 784 mesures (Station Lyon Centre - UID 3028)
- Lille: 783 mesures
- Période: 12/01/2024 au 05/03/2026

### Nettoyage des données
- Suppression des données API obsolètes
- Correction city_id Lille (6 → 10)
- Nullification AQI pour created_at < 05/03/2026
- Suppression mesures avec captured_at < 12/01/2026
- État final: 11,557 mesures validées

### Audit base de données
- Vérification intégrité complète (fact_measures)
- 0 doublons, 0 clés étrangères invalides
- Validation cohérence temporelle
- Détection anomalies PM10 (2 valeurs > 500)

### Organisation projet
- 43 scripts temporaires déplacés vers `scripts/temp/`
- Exclusion Git via `.gitignore`
- Scripts essentiels maintenus dans `scripts/`

---

## Version 2.0 - Migration architecture simplifiée (Février 2026)

### Migration captured_at + dim_date

**SQL**: `sql/migration_add_captured_at.sql`, `sql/create_dim_date.sql`

#### Ajout captured_at dans fact_measures
- Colonne `captured_at TIMESTAMP WITH TIME ZONE` ajoutée
- Migration 5,401 mesures depuis `dim_time.full_date`
- Contrainte NOT NULL et index créés
- Index: `idx_fact_measures_captured_at`, `idx_fact_measures_city_captured`

#### Création dim_date
- Table dimension légère (sans heures)
- 1,461 jours (2024-01-01 → 2027-12-31)
- Format date_id: YYYYMMDD (ex: 20260209)
- Attributs: jour, semaine, mois, trimestre, année, saison

#### Simplification code ETL
- Suppression lookup time_id
- Insertion directe avec captured_at
- Requêtes simplifiées (pas de jointure dim_time)

**Avantages**:
- Code ETL plus simple et rapide
- Requêtes SQL directes sur timestamp
- Performance améliorée (pas de jointure systématique)

---

## Version 1.5 - Stratégie anti-perte de données (Février 2026)

### Fusion optimisée Weather + AQI

**Fichier**: `src/etl_transform_to_db.py`

#### Problème résolu
- Données bloquées quand une API ne répond pas
- Entrées orphelines jamais traitées
- Risque de perte si API down longtemps

#### Solution en 2 temps
1. **Fusion optimale** (< 2h): Groupement par (city_id, heure) pour fusionner weather+AQI
2. **Traitement orphelines** (≥ 2h): Traitement immédiat même si paire manquante

#### Résultats
- 93.8% de fusion complète (weather+AQI)
- 0% de perte de données
- Mesures partielles avec NULL si source manquante

---

## Version 1.4 - Correction timestamps (Février 2026)

### Horodatage authentique

**Date**: 4 février 2026

#### Problème identifié
- Timestamps utilisaient moment de chargement BDD
- Au lieu du moment réel de collecte par APIs

#### Modifications
- `weather_service.py`: Extraction champ `dt` (OpenWeather)
- `air_quality_service.py`: Extraction champ `time.v` (AQICN)
- `data_lake_service.py`: Accepte timestamp optionnel
- `etl_extract_to_lake.py`: Transmission timestamps API
- `etl_transform_to_db.py`: Utilisation timestamp data lake

#### Résultat
- `collected_at` → timestamp API (mesure réelle)
- `captured_at` → timestamp data lake (provenant API)
- Traçabilité précise du moment exact de mesure
- Analyses temporelles fiables

---

## Version 1.3 - Audit complet système (Février 2026)

### Corrections critiques

**Date**: 7 février 2026

#### Sécurité
- Création `.env.example` (référentiel sans clés)
- Mise à jour `.gitignore` (patterns Python, IDE, logs)
- Suppression variable AWS_REGION inutilisée

#### Documentation
- Mise à jour architecture 2 pipelines (Extract + Transform)
- Correction références fichiers obsolètes
- Suppression mentions `scheduler.py`, `test_connections.py`

#### Points forts identifiés
- Architecture Data Lake excellente (JSONB/relationnel)
- Traçabilité via raw_weather_id et raw_aqi_id
- Fusion météo+AQI réussie (-50% doublons, -96% NULL)
- GitHub Actions opérationnel (exécution horaire)

---

## Version 1.2 - Modèle en étoile (Février 2026)

### Déploiement Star Schema

**SQL**: `sql/star_schema.sql`, `sql/migrate_to_star_schema.sql`

#### Tables de dimensions
- `dim_time`: 26,000 périodes (2024-2027, granularité horaire)
- `dim_city`: 10 villes françaises + métadonnées géo
- `dim_weather_condition`: 40+ conditions OpenWeather
- `dim_air_quality_level`: 6 niveaux EPA (Good → Hazardous)

#### Table de faits
- `fact_measures`: Mesures environnementales agrégées
- Métriques météo: température, humidité, pression, vent, nuages
- Métriques AQI: PM2.5, PM10, NO2, O3, SO2, CO
- Références dimensions via FK
- Traçabilité vers data lake (raw_weather_id, raw_aqi_id)

#### Migration
- Migration zéro-perte depuis modèle normalisé
- Remplissage automatique dimensions
- Vérifications post-migration

#### Requêtes OLAP
- 20+ requêtes analytics (`sql/queries_olap.sql`)
- Analyses temporelles, géographiques, par condition
- Cubes OLAP et corrélations

---

## Version 1.1 - Architecture 2 pipelines (Février 2026)

### Séparation Extract et Transform

#### Pipeline 1: Extract (toutes les heures)
- `etl_extract_to_lake.py`
- APIs → Data Lake (JSONB)
- Stockage brut sans transformation
- GitHub Actions: `.github/workflows/etl-extract.yml`

#### Pipeline 2: Transform (toutes les heures)
- `etl_transform_to_db.py`
- Data Lake → Data Warehouse (Star Schema)
- Groupement city/time, fusion weather+AQI
- Lookup dimensions, insertion fact_measures
- Marquage processed=true
- GitHub Actions: `.github/workflows/etl-transform.yml`

#### Avantages
- Séparation responsabilités
- Retraitement possible depuis data lake
- Tolérance aux pannes (retry indépendant)
- Traçabilité complète

---

## Version 1.0 - MVP (Janvier 2026)

### Fonctionnalités initiales

#### Data Lake
- Table `raw_data_lake` (JSONB)
- Stockage brut OpenWeather + AQICN
- Traçabilité source et timestamp
- Index GIN pour requêtes JSON

#### Data Warehouse
- Modèle normalisé initial
- Tables: `cities`, `measures`
- ETL monolithique

#### APIs
- OpenWeather: météo 10 villes
- AQICN: qualité air 10 villes
- Collecte manuelle

#### Infrastructure
- Supabase PostgreSQL (eu-central-1)
- Python 3.12+
- Structure projet modulaire
