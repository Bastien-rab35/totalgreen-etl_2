#!/usr/bin/env bash
set -euo pipefail

# Provision Scaleway Serverless Jobs for TotalGreen ETL.
# Usage:
#   1) Fill variables below (or export them before running).
#   2) Ensure `scw login` and `scw init` are done.
#   3) Run: bash deploy/scaleway/scw_provision_jobs.sh

REGION="${REGION:-fr-par}"
PROJECT_ID="${PROJECT_ID:-}"
NAMESPACE="${NAMESPACE:-totalgreen}"
IMAGE_NAME="${IMAGE_NAME:-totalgreen-etl}"
IMAGE_TAG="${IMAGE_TAG:-serverless}"
FULL_IMAGE="rg.${REGION}.scw.cloud/${NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"
IMAGE_PLATFORM="${IMAGE_PLATFORM:-linux/amd64}"

# Job sizing (adjust to your workload/plan)
CPU_LIMIT="${CPU_LIMIT:-500}"
MEMORY_LIMIT="${MEMORY_LIMIT:-1024}"
LOCAL_STORAGE_CAPACITY="${LOCAL_STORAGE_CAPACITY:-1024}"
JOB_TIMEOUT="${JOB_TIMEOUT:-900s}"

# Required runtime secrets
OPENWEATHER_API_KEY="${OPENWEATHER_API_KEY:-}"
AQICN_API_KEY="${AQICN_API_KEY:-}"
TOMTOM_API_KEY="${TOMTOM_API_KEY:-}"

SUPABASE_URL="${SUPABASE_URL:-}"
SUPABASE_KEY="${SUPABASE_KEY:-}"

# Validation defaults
VALIDATION_HOURS="${VALIDATION_HOURS:-24}"
VALIDATION_STRICT="${VALIDATION_STRICT:-false}"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing command: $1" >&2
    exit 1
  }
}

require_cmd scw
require_cmd docker
require_cmd jq

if [[ -z "$PROJECT_ID" ]]; then
  echo "PROJECT_ID is required. Example:" >&2
  echo "  scw account project list" >&2
  echo "  PROJECT_ID=<project-id> bash deploy/scaleway/scw_provision_jobs.sh" >&2
  exit 1
fi

for required_var in OPENWEATHER_API_KEY AQICN_API_KEY TOMTOM_API_KEY SUPABASE_URL SUPABASE_KEY; do
  if [[ -z "${!required_var}" ]]; then
    echo "Missing env var: ${required_var}" >&2
    exit 1
  fi
done

echo "==> 1) Ensure registry namespace exists: ${NAMESPACE}"
NAMESPACE_ID="$(scw registry namespace list region="$REGION" project-id="$PROJECT_ID" name="$NAMESPACE" -o json | jq -r 'if type=="array" then (.[0].id // empty) else (.namespaces[0].id // empty) end')"
if [[ -z "$NAMESPACE_ID" ]]; then
  NAMESPACE_ID="$(scw registry namespace create region="$REGION" project-id="$PROJECT_ID" name="$NAMESPACE" -o json | jq -r '.id')"
fi
echo "Namespace ID: ${NAMESPACE_ID}"

echo "==> 2) Build and push image: ${FULL_IMAGE}"
scw registry login region="$REGION"
# Sur Apple Silicon, forcer linux/amd64 evite les erreurs de pull sur l'infra serverless.
docker buildx build --platform "${IMAGE_PLATFORM}" -f Dockerfile.serverless -t "${FULL_IMAGE}" --push .

create_or_update_secret() {
  local name="$1"
  local value="$2"

  local secret_id
  secret_id="$(scw secret secret list region="$REGION" project-id="$PROJECT_ID" name="$name" -o json | jq -r 'if type=="array" then (.[0].id // empty) else (.secrets[0].id // empty) end')"

  if [[ -z "$secret_id" ]]; then
    secret_id="$(scw secret secret create region="$REGION" project-id="$PROJECT_ID" name="$name" type=opaque -o json | jq -r '.id')"
  fi

  scw secret version create "$secret_id" region="$REGION" data="$value" disable-previous=true >/dev/null
  echo "$secret_id"
}

echo "==> 3) Create/update secrets in Secret Manager"
SECRET_OPENWEATHER_ID="$(create_or_update_secret OPENWEATHER_API_KEY "$OPENWEATHER_API_KEY")"
SECRET_AQICN_ID="$(create_or_update_secret AQICN_API_KEY "$AQICN_API_KEY")"
SECRET_TOMTOM_ID="$(create_or_update_secret TOMTOM_API_KEY "$TOMTOM_API_KEY")"

SECRET_SUPABASE_URL_ID="$(create_or_update_secret SUPABASE_URL "$SUPABASE_URL")"
SECRET_SUPABASE_KEY_ID="$(create_or_update_secret SUPABASE_KEY "$SUPABASE_KEY")"

ensure_definition() {
  local name="$1"
  local job_type="$2"
  local cron_expr="$3"

  local def_id
  def_id="$(scw jobs definition list region="$REGION" project-id="$PROJECT_ID" -o json | jq -r --arg name "$name" 'if type=="array" then .[] else .job_definitions[] end | select(.name == $name) | .id' | head -n 1)"

  if [[ -z "$def_id" ]]; then
    def_id="$(scw jobs definition create \
      region="$REGION" \
      project-id="$PROJECT_ID" \
      name="$name" \
      image-uri="$FULL_IMAGE" \
      cpu-limit="$CPU_LIMIT" \
      memory-limit="$MEMORY_LIMIT" \
      local-storage-capacity="$LOCAL_STORAGE_CAPACITY" \
      job-timeout="$JOB_TIMEOUT" \
      cron-schedule.schedule="$cron_expr" \
      cron-schedule.timezone="Europe/Paris" \
      environment-variables.JOB_TYPE="$job_type" \
      -o json | jq -r '.id')"
  else
    scw jobs definition update "$def_id" \
      region="$REGION" \
      image-uri="$FULL_IMAGE" \
      cpu-limit="$CPU_LIMIT" \
      memory-limit="$MEMORY_LIMIT" \
      local-storage-capacity="$LOCAL_STORAGE_CAPACITY" \
      job-timeout="$JOB_TIMEOUT" \
      cron-schedule.schedule="$cron_expr" \
      cron-schedule.timezone="Europe/Paris" \
      environment-variables.JOB_TYPE="$job_type" >/dev/null
  fi

  if [[ -z "$def_id" ]]; then
    echo "Failed to create/update job definition: $name" >&2
    exit 1
  fi

  echo "$def_id"
}

ensure_secret_binding() {
  local def_id="$1"
  local secret_id="$2"
  local env_name="$3"
  local secret_revision

  secret_revision="$(scw secret version list "$secret_id" region="$REGION" -o json | jq -r '
    if type=="array" then
      (if length > 0 then (([.[] | select(.latest == true)][0].revision) // (max_by(.revision).revision)) else empty end)
    else
      (if (.versions | length) > 0 then ((([.versions[] | select(.latest == true)][0].revision) // (.versions | max_by(.revision).revision))) else empty end)
    end
  ' )"

  if [[ -z "$secret_revision" ]]; then
    echo "Failed to find latest revision for secret: $secret_id" >&2
    exit 1
  fi

  local refs_json
  refs_json="$(scw jobs secret list region="$REGION" job-definition-id="$def_id" -o json)"

  local existing_ids
  existing_ids="$(echo "$refs_json" | jq -r --arg env "$env_name" '
    if type=="array" then
      .[]? | select((.env_var.name // .env_var_name // "") == $env) | .secret_id
    else
      .secrets[]? | select((.env_var.name // .env_var_name // "") == $env) | .secret_id
    end
  ')"

  if [[ -z "$existing_ids" ]]; then
    scw jobs secret create \
      region="$REGION" \
      job-definition-id="$def_id" \
      secrets.0.secret-manager-id="$secret_id" \
      secrets.0.secret-manager-version="$secret_revision" \
      secrets.0.env-var-name="$env_name" >/dev/null
  else
    local first_id=""
    while IFS= read -r ref_id; do
      [[ -z "$ref_id" ]] && continue
      if [[ -z "$first_id" ]]; then
        first_id="$ref_id"
        scw jobs secret update \
          region="$REGION" \
          secret-id="$ref_id" \
          secret-manager-version="$secret_revision" \
          env-var-name="$env_name" >/dev/null
      else
        # Nettoie les doublons eventuels sur la meme variable d'environnement.
        scw jobs secret delete region="$REGION" secret-id="$ref_id" >/dev/null
      fi
    done <<< "$existing_ids"
  fi
}

echo "==> 4) Create/update the 3 job definitions"
DEF_EXTRACT="$(ensure_definition totalgreen-etl-extract extract '0 * * * *')"
DEF_TRANSFORM="$(ensure_definition totalgreen-etl-transform transform '5 * * * *')"
DEF_VALIDATE="$(ensure_definition totalgreen-etl-validate validate '15 0,12 * * *')"

echo "==> 5) Add validation-specific env vars"
scw jobs definition update "$DEF_VALIDATE" \
  region="$REGION" \
  environment-variables.JOB_TYPE=validate \
  environment-variables.VALIDATION_HOURS="$VALIDATION_HOURS" \
  environment-variables.VALIDATION_STRICT="$VALIDATION_STRICT" >/dev/null

echo "==> 6) Attach runtime secrets to all jobs"
for def_id in "$DEF_EXTRACT" "$DEF_TRANSFORM" "$DEF_VALIDATE"; do
  ensure_secret_binding "$def_id" "$SECRET_OPENWEATHER_ID" OPENWEATHER_API_KEY
  ensure_secret_binding "$def_id" "$SECRET_AQICN_ID" AQICN_API_KEY
  ensure_secret_binding "$def_id" "$SECRET_TOMTOM_ID" TOMTOM_API_KEY

  ensure_secret_binding "$def_id" "$SECRET_SUPABASE_URL_ID" SUPABASE_URL
  ensure_secret_binding "$def_id" "$SECRET_SUPABASE_KEY_ID" SUPABASE_KEY
done

echo "==> Done"
echo "Definitions:"
echo "  extract:   $DEF_EXTRACT"
echo "  transform: $DEF_TRANSFORM"
echo "  validate:  $DEF_VALIDATE"

echo
echo "Smoke tests (manual starts):"
echo "  scw jobs definition start ${DEF_EXTRACT} region=${REGION}"
echo "  scw jobs definition start ${DEF_TRANSFORM} region=${REGION}"
echo "  scw jobs definition start ${DEF_VALIDATE} region=${REGION}"
