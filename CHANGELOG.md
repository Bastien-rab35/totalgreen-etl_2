# Changelog - TotalGreen ETL

Historique des evolutions principales du projet.

## 2.6.0 - Implémentation Extract & Transform via TomTom & Hub'Eau (16 avril 2026)
- **TomTom Service** : Ajout de l'extraction API du trafic routier (`tomtom_flow`) et des incidents (`tomtom_incidents`) avec bounding box par ville, gestion des quotas 429 et calcul de KPI sur la congestion.
- **Hub'Eau Service** : Ajout de l'extraction API des nappes phréatiques (stations et `chroniques_tr` Temps Réel), gestion de la pagination et de la bounding box.
- **ETL Extract** : Intégration de ces deux services à l'extracteur global (`etl_extract_to_lake.py`) avec stockage dans Supabase sous forme de JSON brut.
- **ETL Transform** : Modification de la transformation combinée (`etl_transform_to_db.py`) pour traiter analytiquement le trafic et l'eau. Ajout de la formule mathématique `incident_severity_score` et du dimensionnement `_resolve_date_and_hour`.
- **Database Service** : Intégration et requêtage vers les 5 nouvelles tables (`dim_traffic_point`, `dim_incident_category`, `fact_traffic_flow_hourly`, etc.).

## 2.5.1 - Cadrage integration TomTom et Hub Eau (15 avril 2026)

- Ajout du mapping SQL cible pour l'integration Traffic (TomTom) et Piezometrie (Hub Eau):
  - `sql/mspr2_traffic_groundwater_schema.sql`
- Ajout du contrat d'extraction JSON normalise pour les 2 APIs:
  - `docs/CONTRAT_EXTRACTION_TOMTOM_HUBEAU_MSPR2.md`
- Formalisation des KPIs metier cibles:
  - `congestion_ratio`, `speed_ratio`, `incident_severity_score`
  - `groundwater_level_ngf`, `groundwater_depth`, `groundwater_trend_7d`, `anomaly_score`

## 2.5.0 - Baseline MSPR2 et nouveau depot GitHub (15 avril 2026)

- Initialisation du depot MSPR2 sur `Bastien-rab35/totalgreen-etl_2` avec historique propre.
- Separation explicite du perimetre MSPR2 vis-a-vis de l'historique MSPR1.
- Harmonisation des references projet (README, changelog, workflows CI).
- Preparation de la roadmap technique MSPR2 (milestones + backlog d'issues techniques).

## 2.4.1 - Mise a jour documentation (26 mars 2026)

- Relecture complete et harmonisation de tous les fichiers `.md` du depot.
- Suppression des references obsoletes vers des fichiers non presents.
- Alignement des guides sur l'execution actuelle:
  - jobs Scaleway (`extract`, `transform`, `validate`)
  - scripts SQL presents dans `sql/`
  - scripts Python presents dans `scripts/`
- Clarification du perimetre entre architecture historique (`dim_time`) et architecture cible (`dim_date`).

## 2.4.0 - Migration vers Scaleway Serverless (26 mars 2026)

- Ajout de `Dockerfile.serverless` pour executer les jobs ETL.
- Ajout de `scripts/scaleway/run_job.sh` (dispatch `JOB_TYPE`).
- Ajout du guide `docs/SCALEWAY_SERVERLESS.md`.
- Ajout des assets de provisioning:
  - `deploy/scaleway/scw_provision_jobs.sh`
  - `deploy/scaleway/.env.example`

## 2.3.2 - Correction UTC et coherence temporelle (6 mars 2026)

- Standardisation des timestamps ISO 8601 avec timezone explicite.
- Correction des incoherences detectees dans la validation qualite.
- Fichiers principalement touches:
  - `src/services/data_lake_service.py`
  - `src/services/database_service.py`
  - `src/etl_transform_to_db.py`

## 2.3.0 - Stockage des anomalies en base (6 mars 2026)

- Ajout de `sql/anomalies_table.sql`.
- Ajout de `sql/migrate_anomalies_table.sql` pour migration d'ancien schema.
- Enregistrement des anomalies depuis `scripts/validate_data_quality.py`.

## 2.2.0 - Optimisation AQI et simplification (mars 2026)

- Ajustement des stations AQICN pour plusieurs villes (dont Lyon et Lille).
- Nettoyage des composants ML/SQL non conserves.
- Mise a jour de `data/cities_reference.json` et des scripts ETL associes.

## 2.1.0 - Import historique AQICN (mars 2026)

- Ajout du flux d'import CSV via `scripts/import_aqicn_historical.py`.
- Ajout du traitement batch via `scripts/process_all_remaining.py`.

## 2.0.0 - Star schema et simplification temporelle (fevrier 2026)

- Structuration du DWH autour de `fact_measures` et dimensions.
- Introduction de `dim_date` via `sql/create_dim_date.sql`.

## 1.x - Fondation du projet (janvier-fevrier 2026)

- Mise en place du Data Lake JSONB (`raw_data_lake`).
- Separation des pipelines extract / transform.
- Premiere version de l'automatisation et des controles de qualite.
