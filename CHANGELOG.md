# Historique des modifications - TotalGreen ETL

Ce document retrace les principales évolutions techniques du projet.

---

## Version 2.4.0 - Migration vers Scaleway Serverless (26 Mars 2026)

### Orchestration
- Ajout d'un conteneur dédié `Dockerfile.serverless` pour exécuter les jobs ETL.
- Ajout du script `scripts/scaleway/run_job.sh` pour dispatcher les 3 exécutions:
  - `extract`
  - `transform`
  - `validate`
- Ajout de `.dockerignore` pour réduire la taille de l'image.

### Déploiement et documentation
- Ajout du guide `docs/SCALEWAY_SERVERLESS.md`.
- Ajout du template de variables `deploy/scaleway/.env.example`.
- Mise à jour des docs principales pour remplacer l'orchestration GitHub Actions par Scaleway Serverless Jobs + Cron.

### Stratégie de bascule
- Conservation des workflows GitHub en mode transition (double run recommandé).
- Plan de rollback documenté en cas d'incident.

---

## Version 2.3.2 - Correction timestamps UTC (6 Mars 2026)

### Problème identifié
- **55 mesures avec created_at < captured_at** (incohérence temporelle impossible)
- Cause : `datetime.utcnow()` génère timestamp **sans fuseau horaire explicite**
- Exemple : `2026-03-05T14:03:19.591448` au lieu de `2026-03-05T14:03:19.591448+00:00`

### Solution appliquée
- **Remplacement** `datetime.utcnow()` → `datetime.now(timezone.utc)`
- **Import** `from datetime import datetime, timezone` ajouté
- **Format ISO 8601 complet** : tous les timestamps incluent maintenant `+00:00`

### Fichiers corrigés
- `src/services/database_service.py` : `captured_at`, `execution_time`
- `src/etl_transform_to_db.py` : `captured_at` dans transform
- `src/services/data_lake_service.py` : `collected_at`, `processed_at`

### Impact
- ✅ Résout l'incohérence temporelle détectée par `validate_data_quality.py`
- ✅ Conformité ISO 8601 stricte (timezone explicite)
- ✅ Compatibilité PostgreSQL TIMESTAMPTZ améliorée

---

## Version 2.3 - Stockage des anomalies en BDD (6 Mars 2026)

### Table anomalies
- **Création** : Nouvelle table `anomalies` pour tracer les problèmes de qualité des données
  - Colonnes : validation_run_id (UUID), severity, category, message, details (JSONB), detected_at
  - Index sur run_id, severity, category, detected_at pour optimiser les requêtes
  - Vue `anomalies_daily_stats` pour statistiques quotidiennes

### Script validate_data_quality.py
- **Sauvegarde automatique** des anomalies détectées dans la table BDD
  - Génération d'un UUID unique par run de validation
  - Stockage de toutes les anomalies (critical, warning, info)
  - Conservation des détails en JSONB (exemples, statistiques, villes impactées)
- **Traçabilité** : Historique complet des problèmes de qualité

### Correctif - Migration table anomalies
- **Problème** : Table `anomalies` existe avec ancien schéma ML (colonnes incompatibles)
- **Solution** : Script de migration `sql/migrate_anomalies_table.sql`
  - Supprime l'ancienne table et recrée avec nouveau schéma
  - ⚠️ **ACTION REQUISE** : Exécuter ce script dans Supabase SQL Editor
- **Instructions détaillées** : Voir `MIGRATION_ANOMALIES.md`
- **Test** : Script `scripts/test_anomalies_table.py` pour vérifier le bon fonctionnement

### Fichiers
- **Nouveau** : `sql/anomalies_table.sql` (schéma table + vue stats)
- **Nouveau** : `sql/migrate_anomalies_table.sql` (migration ancien → nouveau schéma)
- **Nouveau** : `scripts/test_anomalies_table.py` (test de la table)
- **Nouveau** : `MIGRATION_ANOMALIES.md` (guide de migration)
- **Modifié** : `scripts/validate_data_quality.py` (méthode save_anomalies_to_db)
- **Mis à jour** : `sql/README.md` (documentation table anomalies)

---

## Version 2.2 - Optimisation stations AQI et simplification ML (6 Mars 2026)

### Optimisation des stations AQICN
- **Lyon** : Passage à la station `france/rhonealpes/rhone/lyon-centre` (idx 3028)
  - Données actualisées en temps réel
  - Meilleure couverture des polluants (PM2.5, PM10, NO2, O3)
- **Lille** : Remplacement @8613 (obsolète) par `roubaix`
  - Station Roubaix Serres (métropole lilloise, ~16 km)
  - Données actuelles et fiables
  - AQI et polluants complets disponibles

### Simplification architecture ML
- **Suppression** des fichiers SQL ML :
  - `sql/anomaly_detection_schema.sql` (table anomalies, ml_model_metadata)
  - `sql/anomaly_functions.sql` (fonctions get_city_stats, get_anomaly_summary)
  - `docs/ANOMALY_DETECTION.md`
- **Conservation** du script Python de validation qualité :
  - `scripts/validate_data_quality.py` (5 niveaux de validation)
  - Exécution 2×/jour via GitHub Actions
  - Détection doublons, incohérences, outliers statistiques

### Mise à jour configuration
- **Fichier** : `data/cities_reference.json`
  - Ajout champ `aqi_station` pour chaque ville
  - Configuration spécifique Lyon et Lille
- **SQL** : `sql/update_cities_aqi_stations.sql`
  - Script de mise à jour des stations dans dim_city

### Documentation
- Mise à jour README.md (focus validation qualité Python)
- Mise à jour SLIDE_DEVELOPPEMENT.md
- Mise à jour docs/README.md, docs/ARCHITECTURE.md, sql/README.md

### Fichiers modifiés
- `data/cities_reference.json`
- `src/services/air_quality_service.py` (paramètre aqi_station)
- `src/etl_extract_to_lake.py`, `src/etl_pipeline.py`
- `sql/UPDATE_FUNCTIONS.sql`
- Tous les fichiers .md de documentation

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
