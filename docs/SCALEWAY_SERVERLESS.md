# Migration GitHub Actions -> Scaleway Serverless

Ce guide remplace l'orchestration GitHub Actions par Scaleway Serverless Jobs + Cron Triggers.

## Objectif

- Exécuter les pipelines ETL en region UE via Scaleway.
- Centraliser les secrets dans Scaleway Secret Manager.
- Conserver les mêmes scripts Python et les mêmes crons fonctionnels.

## Prerequis

- Un compte Scaleway.
- Une organisation et un projet Scaleway.
- Docker local (build image).
- Variables sensibles disponibles:
  - `OPENWEATHER_API_KEY`
  - `AQICN_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`

## 1. Construire l'image

L'image est definie dans `Dockerfile.serverless`.

```bash
docker build -f Dockerfile.serverless -t totalgreen-etl:serverless .
```

## 2. Publier l'image sur Scaleway Container Registry

Publiez l'image dans un namespace registry Scaleway (UI ou CLI `scw`).

Image a utiliser ensuite dans les jobs:
- `rg.fr-par.scw.cloud/<namespace>/totalgreen-etl:serverless`

## 3. Creer les secrets dans Scaleway

Creer 4 secrets (meme noms que les variables d'environnement):
- `OPENWEATHER_API_KEY`
- `AQICN_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`

Puis injecter ces secrets en variables d'environnement dans chaque job.

## 4. Creer les 3 jobs serverless

Tous les jobs reutilisent la meme image et le meme `CMD`.
Le comportement est pilote par la variable `JOB_TYPE`.

### Job 1 - Extract

- `JOB_TYPE=extract`
- Cron: `0 * * * *`

### Job 2 - Transform

- `JOB_TYPE=transform`
- Cron recommande: `5 * * * *`
- Pourquoi +5 min: evite d'executer transform avant la fin d'extract.

### Job 3 - Data Quality

- `JOB_TYPE=validate`
- `VALIDATION_HOURS=24`
- `VALIDATION_STRICT=false`
- Cron: `15 0,12 * * *`

## 5. Mapping des workflows existants

- `.github/workflows/etl-extract.yml` -> Job `extract`
- `.github/workflows/etl-transform.yml` -> Job `transform`
- `.github/workflows/data-quality-validation.yml` -> Job `validate`

## 6. Double run recommande

Pendant 1 a 2 semaines:

- Conserver GitHub Actions actives.
- Activer en parallele Scaleway Jobs.
- Comparer les volumes et resultats:
  - nombre d'enregistrements `raw_data_lake`
  - nombre d'enregistrements `fact_measures`
  - anomalies detectees

Quand les resultats sont stables, desactiver les workflows GitHub.

## 7. Rollback

En cas de probleme:

1. Suspendre les Cron Triggers Scaleway.
2. Reactiver les workflows `.github/workflows/*`.
3. Inspecter les logs du job en erreur et corriger.

## Provisioning automatise (CLI)

Un script pret a l'emploi est disponible:
- `deploy/scaleway/scw_provision_jobs.sh`

Il automatise:
- creation du namespace registry
- build/push de l'image
- creation/mise a jour des secrets
- creation/mise a jour des 3 definitions de jobs + CRON
- association des secrets aux jobs

Exemple d'execution:

```bash
export PROJECT_ID="<votre-project-id>"
export OPENWEATHER_API_KEY="<...>"
export AQICN_API_KEY="<...>"
export SUPABASE_URL="https://...supabase.co"
export SUPABASE_KEY="<...>"

# Recommande sur Mac Apple Silicon
export IMAGE_PLATFORM="linux/amd64"

bash deploy/scaleway/scw_provision_jobs.sh
```

## Notes importantes

- Les scripts ETL ecrivent des logs dans `/app/logs` dans le conteneur.
- Les logs de reference operationnelle restent ceux de Scaleway (stdout/stderr).
- Aucune cle ne doit etre committee dans Git.
