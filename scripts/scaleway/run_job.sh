#!/usr/bin/env sh
set -eu

# Dispatcher unique pour réutiliser la même image Docker avec plusieurs jobs.
JOB_TYPE="${JOB_TYPE:-extract}"

case "$JOB_TYPE" in
  extract)
    echo "[serverless] Running extract job"
    cd /app/src
    exec python etl_extract_to_lake.py
    ;;
  transform)
    echo "[serverless] Running transform job"
    cd /app/src
    exec python etl_transform_to_db.py
    ;;
  validate)
    echo "[serverless] Running data-quality validation job"
    HOURS="${VALIDATION_HOURS:-24}"
    STRICT_FLAG=""
    if [ "${VALIDATION_STRICT:-false}" = "true" ]; then
      STRICT_FLAG="--strict"
    fi
    cd /app
    exec python scripts/validate_data_quality.py --hours "$HOURS" $STRICT_FLAG
    ;;
  *)
    echo "[serverless] Unknown JOB_TYPE='$JOB_TYPE' (expected: extract|transform|validate)" >&2
    exit 64
    ;;
esac
