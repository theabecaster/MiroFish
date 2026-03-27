#!/usr/bin/env bash
set -euo pipefail

# Start gunicorn in the background
echo "[entrypoint] Starting gunicorn..."
gunicorn --bind 0.0.0.0:5001 --workers 1 --threads 4 --timeout 7200 run:app &
GUNICORN_PID=$!

# Wait for MiroFish to be healthy
echo "[entrypoint] Waiting for MiroFish health check..."
for i in $(seq 1 60); do
  if curl -sf http://localhost:5001/health > /dev/null 2>&1; then
    echo "[entrypoint] MiroFish healthy after ${i}s"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "[entrypoint] MiroFish health check timed out after 60s"
    kill $GUNICORN_PID 2>/dev/null || true
    exit 1
  fi
  sleep 1
done

# If SIM_ID is set, decode and run the pipeline script, then exit
if [ -n "${SIM_ID:-}" ]; then
  echo "[entrypoint] SIM_ID=${SIM_ID} — running pipeline"

  if [ -z "${PIPELINE_SCRIPT_B64:-}" ]; then
    echo "[entrypoint] ERROR: PIPELINE_SCRIPT_B64 env var not set"
    kill $GUNICORN_PID 2>/dev/null || true
    exit 1
  fi

  # Decode the pipeline runner script from base64
  echo "$PIPELINE_SCRIPT_B64" | base64 -d > /tmp/pipeline-runner.mjs

  # Run the pipeline — exit code propagates
  node /tmp/pipeline-runner.mjs
  EXIT_CODE=$?

  echo "[entrypoint] Pipeline exited with code ${EXIT_CODE}"
  kill $GUNICORN_PID 2>/dev/null || true
  exit $EXIT_CODE
fi

# No SIM_ID — normal deploy machine, keep gunicorn in foreground
echo "[entrypoint] No SIM_ID — running as normal MiroFish server"
wait $GUNICORN_PID
