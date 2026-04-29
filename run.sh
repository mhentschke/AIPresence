#!/usr/bin/env bash
set -e

# --- Supervisor auto-discovery ---
# When homeassistant_api: true is set in config.yaml, the Supervisor
# injects SUPERVISOR_TOKEN which works as a HA API bearer token.
if [ -n "$SUPERVISOR_TOKEN" ]; then
    export HA_URL="http://supervisor/core/api"
    export HA_TOKEN="$SUPERVISOR_TOKEN"
fi

# --- Read add-on options from Supervisor-managed file ---
OPTIONS_FILE="/data/options.json"
if [ -f "$OPTIONS_FILE" ]; then
    export SAMPLE_RATE=$(jq -r '.sample_rate // 2.0' "$OPTIONS_FILE")
    export MINIMUM_TRAINING_SAMPLES=$(jq -r '.minimum_training_samples // 200' "$OPTIONS_FILE")
    export LOG_LEVEL=$(jq -r '.log_level // "INFO"' "$OPTIONS_FILE")
fi

# --- Persistence directory ---
export DATA_PATH="${DATA_PATH:-/data}"
mkdir -p "$DATA_PATH"

# --- Start backend ---
# Use exec so uvicorn becomes PID 1 and receives signals properly.
# INGRESS_PORT is set by the Supervisor; default to 8099 for standalone use.
# Lowercase LOG_LEVEL for uvicorn (HA options use uppercase).
UVICORN_LOG_LEVEL=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')
exec uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port "${INGRESS_PORT:-8099}" \
    --log-level "$UVICORN_LOG_LEVEL"
