# Architecture Technique - TotalGreen ETL

Ce document decrit l'architecture fonctionnelle et technique actuelle du projet pour 10 grandes villes françaises.

## Vue globale

Le systeme suit un flux ETL en 3 etapes:

```text
OpenWeather + AQICN + TomTom + Hub'Eau
        |
        v
Extract -> raw_data_lake (JSONB)
        |
        v
Transform -> fact_measures + trafic + eaux souterraines + dimensions
        |
        v
Validate -> controle qualite + table anomalies
```

## Composants principaux

### Data Lake

- Table de stockage brut: `raw_data_lake`
- Format: JSONB (payload API conserve)
- Champs utilises par le pipeline:
  - `city_id`, `city_name`, `source`, `raw_data`
  - `collected_at`, `processed`, `processed_at`

### Data Warehouse

- Tables de faits: 
  - `fact_measures` (Météo & Qualité de l'air)
  - `fact_traffic_flow` & `fact_traffic_incidents` (TomTom)
  - `fact_groundwater_realtime` (Hub'Eau)
- Dimensions principales:
  - `dim_city`
  - `dim_weather_condition`
  - `dim_air_quality_level`
  - `dim_time` (historique)
  - `dim_date` (architecture cible simplifiee)

### Controle qualite

- Script: `scripts/validate_data_quality.py`
- Verifications:
  - integrite structurelle
  - coherence temporelle
  - limites physiques
  - couverture des villes
  - outliers statistiques
- Persistences des resultats: table `anomalies`

## Pipelines

### 1) Extract (`src/etl_extract_to_lake.py`)

- Lit le referentiel des villes depuis la base.
- Interroge OpenWeather, AQICN, TomTom et Hub'Eau (chroniques temps réel limitées aux dernières 24h pour préserver le stockage).
- Stocke les reponses brutes dans `raw_data_lake`.
- Marque le statut des extractions via logs ETL.

### 2) Transform (`src/etl_transform_to_db.py`)

- Lit les enregistrements non traites (`processed = false`) par larges paquets (batch_size de 1000).
- Groupe les donnees par ville et plage temporelle.
- Fusionne meteo + qualite de l'air quand possible, charge le trafic et l'eau séparément avec gestion silencieuse des conflits PostgreSQL.
- Charge dans les schemas analytiques respectifs.
- Marque les lignes source en `processed = true`.

### 3) Validate (`scripts/validate_data_quality.py`)

- Validation étendue sur l'ensemble des tables de faits (`fact_measures`, `fact_traffic_flow_hourly`, `fact_traffic_incident_hourly`, `fact_groundwater_realtime`).
- Vérifie l'intégrité de la structure, la temporalité, la couverture spatiale, les outliers statistiques et les limites métiers des variables (ex: trafic congestionné, hauteur des nappes, PM10).
- Analyse une fenetre temporelle (`--hours`, defaut 24).
- Retourne un code de sortie d'exploitation.
- Sauvegarde les anomalies detectees (severity/category/details).

## Modele temporel: historique vs cible

Le depot contient deux approches temporelles:

- Historique: `dim_time` + `time_id` (defini dans `sql/star_schema.sql`).
- Cible: `dim_date` (defini dans `sql/create_dim_date.sql`) avec jointure par date de capture.

La documentation privilegie `dim_date` pour les analyses courantes, tout en conservant la compatibilite historique des scripts SQL existants.

## Orchestration

- Runtime serverless: image construite depuis `Dockerfile.serverless`.
- Dispatcher des jobs: `scripts/scaleway/run_job.sh`.
- Types de jobs:
  - `extract`
  - `transform`
  - `validate`

Guide detaille: `docs/SCALEWAY_SERVERLESS.md`.

## Securite et conformite

- Aucune donnee personnelle exploitee.
- Secrets portes par variables d'environnement.
- Connexions API et base via TLS.
- Hebergement cible en region UE.

Details: `docs/SECURITE.md`.

## References

- `sql/star_schema.sql`
- `sql/create_dim_date.sql`
- `sql/mspr2_traffic_groundwater_schema.sql`
- `sql/anomalies_table.sql`
- `src/etl_extract_to_lake.py`
- `src/etl_transform_to_db.py`
- `scripts/validate_data_quality.py`

Derniere mise a jour: `17 avril 2026`
