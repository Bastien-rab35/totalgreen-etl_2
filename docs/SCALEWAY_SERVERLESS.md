# Scaleway Serverless

Guide d'exploitation du projet ETL avec Scaleway Serverless Jobs.

## Objectif

Executer les 3 taches (`extract`, `transform`, `validate`) sur une image Docker unique, planifiees par cron et alimentees en secrets via Scaleway Secret Manager.

## Prerequis

- Compte Scaleway avec projet actif.
- CLI `scw` configuree (`scw init`).
- `docker`, `jq` et `bash` disponibles.
- Variables sensibles:
  - `OPENWEATHER_API_KEY`
  - `AQICN_API_KEY`
  - `TOMTOM_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`

## Provisioning recommandé

Script: `deploy/scaleway/scw_provision_jobs.sh`

Ce script realise:

- creation/verification du namespace registry
- build/push de l'image serverless
- creation/mise a jour des secrets
- creation/mise a jour des 3 jobs et cron
- liaison des secrets aux jobs

Exemple:

```bash
export PROJECT_ID="<project-id>"
export OPENWEATHER_API_KEY="<...>"
export AQICN_API_KEY="<...>"
export TOMTOM_API_KEY="<...>"
export SUPABASE_URL="https://<project>.supabase.co"
export SUPABASE_KEY="<...>"

# Recommande sur Mac Apple Silicon
export IMAGE_PLATFORM="linux/amd64"

bash deploy/scaleway/scw_provision_jobs.sh
```

Variables utiles du script:

- `REGION` (defaut `fr-par`)
- `NAMESPACE` (defaut `totalgreen`)
- `IMAGE_NAME` (defaut `totalgreen-etl`)
- `IMAGE_TAG` (defaut `serverless`)
- `VALIDATION_HOURS` (defaut `24`)
- `VALIDATION_STRICT` (defaut `false`)

## Configuration manuelle (si necessaire)

1. Construire et publier l'image `Dockerfile.serverless` dans le registry Scaleway.
2. Creer les 5 secrets (`OPENWEATHER_API_KEY`, `AQICN_API_KEY`, `TOMTOM_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`).
3. Creer 3 definitions de jobs utilisant la meme image et les variables:
   - `JOB_TYPE=extract`, cron `0 * * * *` (extraction API, limite historique Hub'Eau 24h)
   - `JOB_TYPE=transform`, cron `5 * * * *` (transformation en base, limit batch_size=1000)
   - `JOB_TYPE=validate`, cron `15 0,12 * * *`
4. Ajouter sur le job `validate`:
   - `VALIDATION_HOURS=24`
   - `VALIDATION_STRICT=false`

Le dispatch est gere par `scripts/scaleway/run_job.sh`.

## Verification post-deploiement

- Demarrer manuellement chaque job une premiere fois.
- Verifier les logs Scaleway (stdout/stderr).
- Confirmer les effets cote base:
  - nouvelles lignes dans `raw_data_lake`
  - nouvelles lignes dans `fact_measures`
  - nouvelles lignes dans `anomalies` apres validation

## Rollback

1. Mettre les cron Scaleway en pause.
2. Revenir temporairement a une execution locale/planifiee alternative.
3. Corriger l'image, les secrets ou les variables de job.
4. Relancer un smoke test avant reprise du cron.

## Notes d'exploitation

- Les logs applicatifs existent en local dans `logs/`, mais en serverless la source de verite est la sortie du job.
- Ne jamais commiter de cles dans Git.
- Conserver une rotation reguliere des cles API.

Derniere mise a jour: `17 avril 2026`
