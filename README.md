# TotalGreen ETL - MSPR2

Pipeline ETL MSPR2 de collecte et de transformation de donnees environnementales et routières (Météo OpenWeather, Qualite de l'air AQICN, Trafic TomTom, Nappes Phréatiques Hub'Eau) pour 10 villes francaises.

## Vue d'ensemble

Le projet repose sur 3 etapes operationnelles:

1. `extract` : collecte multi-APIs (limité à 24h d'historique pour Hub'Eau afin d'optimiser le volume) et stockage brut dans `raw_data_lake` (JSONB).
2. `transform` : transformation par paquets (batch_size = 1000) et chargement dans le Data Warehouse (tables de faits + dimensions) avec gestion silencieuse des doublons.
3. `validate` : controle qualite des donnees via `scripts/validate_data_quality.py`.

Orchestration cible: Scaleway Serverless Jobs (cron).

## Prerequis

- Python `3.12+`
- Un projet Supabase en region UE
- Cles API:
  - `OPENWEATHER_API_KEY`
  - `AQICN_API_KEY`
  - `TOMTOM_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Creer un fichier `.env` a la racine:

```env
OPENWEATHER_API_KEY=...
AQICN_API_KEY=...
TOMTOM_API_KEY=...
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=...
```

## Initialisation SQL

Dans l'editeur SQL Supabase, executer dans cet ordre:

```sql
-- 1) Schema principal (dimensions + faits + fonctions)
\i sql/star_schema.sql

-- 2) Schema additionnel (Trafic et Eaux souterraines)
\i sql/mspr2_traffic_groundwater_schema.sql

-- 3) Dimension date simplifiee (architecture cible)
\i sql/create_dim_date.sql

-- 4) Table de suivi des anomalies de validation
\i sql/anomalies_table.sql
```

## Execution locale

```bash
# 1) Extraction API -> data lake
python src/etl_extract_to_lake.py

# 2) Transformation data lake -> DWH
python src/etl_transform_to_db.py

# 3) Validation qualite
python scripts/validate_data_quality.py --hours 24

# En cas de retard du Data Lake, forcer une transformation totale:
python scripts/process_all_remaining.py
```

## Orchestration Scaleway

- Image: `Dockerfile.serverless`
- Point d'entree: `scripts/scaleway/run_job.sh`
- Jobs:
  - `JOB_TYPE=extract` (cron `0 * * * *`)
  - `JOB_TYPE=transform` (cron `5 * * * *` - paquets de 1000 lignes)
  - `JOB_TYPE=validate` (cron `15 0,12 * * *`)

Provisioning automatise disponible via `deploy/scaleway/scw_provision_jobs.sh`.

Details: `docs/SCALEWAY_SERVERLESS.md`.

## Structure du projet

```text
MSPR 2/
├── CHANGELOG.md
├── Dockerfile.serverless
├── README.md
├── requirements.txt
├── data/
│   └── cities_reference.json
├── deploy/scaleway/
│   ├── .env.example
│   └── scw_provision_jobs.sh
├── docs/
│   ├── ARCHITECTURE.md
│   ├── README.md
│   ├── SCALEWAY_SERVERLESS.md
│   └── SECURITE.md
├── scripts/
│   ├── cleanup_data_quality_issues.py
│   ├── import_aqicn_historical.py
│   ├── process_all_remaining.py
│   ├── test_performance.py
│   ├── validate_data_quality.py
│   └── scaleway/run_job.sh
├── sql/
│   ├── README.md
│   ├── UPDATE_FUNCTIONS.sql
│   ├── anomalies_table.sql
│   ├── create_dim_date.sql
│   ├── migrate_anomalies_table.sql
│   ├── queries_olap.sql
│   ├── mspr2_traffic_groundwater_schema.sql
│   └── star_schema.sql
└── src/
    ├── config.py
    ├── etl_extract_to_lake.py
    ├── etl_pipeline.py
    ├── etl_transform_to_db.py
    └── services/
```

## Depannage rapide

Verifier la configuration:

```bash
python -c "from src.config import config; config.validate(); print('OK')"
```

Verifier les non-traites dans le data lake:

```sql
SELECT source, COUNT(*) AS pending
FROM raw_data_lake
WHERE processed = false
GROUP BY source;
```

## Documentation

- `docs/README.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITE.md`
- `docs/SCALEWAY_SERVERLESS.md`
- `scripts/README.md`
- `sql/README.md`
- `CHANGELOG.md`

## Version

- Version documentaire: `2.6.0`
- Derniere mise a jour: `17 avril 2026`
