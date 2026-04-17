# Scripts - TotalGreen ETL

Ce dossier regroupe les scripts d'exploitation utilises autour des pipelines ETL.

## Scripts disponibles

- `import_aqicn_historical.py`
  - Importe des donnees historiques AQICN depuis CSV.
  - Alimente `raw_data_lake` pour traitement ensuite.

- `process_all_remaining.py`
  - Traite toutes les entrees restantes du data lake (`processed = false`).
  - Pratique apres un import massif.

- `validate_data_quality.py`
  - Lance les controles qualite sur toutes les tables de faits (`fact_measures`, `fact_traffic_flow_hourly`, `fact_traffic_incident_hourly`, `fact_groundwater_realtime`).
  - Ecrit les anomalies dans la table `anomalies`.

- `cleanup_data_quality_issues.py`
  - Corrige/supprime certains problemes detectes (doublons, dates futures, etc.).
  - Supporte un mode simulation (`--dry-run`).

- `test_performance.py`
  - Script de test de performance ETL.

- `scaleway/run_job.sh`
  - Dispatcher shell utilise en serverless.
  - Route vers `extract`, `transform` ou `validate` selon `JOB_TYPE`.

## Exemples d'utilisation

```bash
source venv/bin/activate

# Import historique
python scripts/import_aqicn_historical.py --insert

# Traitement backlog
python scripts/process_all_remaining.py

# Validation 24h
python scripts/validate_data_quality.py --hours 24

# Validation stricte 48h
python scripts/validate_data_quality.py --hours 48 --strict

# Nettoyage en simulation
python scripts/cleanup_data_quality_issues.py --dry-run
```

## Bonnes pratiques

- Lancer `validate_data_quality.py` apres les runs ETL importants.
- Conserver les scripts ad hoc de diagnostic hors versionnage si temporaires.
- Executer les operations de nettoyage en `--dry-run` avant mode reel.

Derniere mise a jour: `17 avril 2026`

