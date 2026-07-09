#!/bin/bash
set -e

echo "===== Rasa Startup at $(date -u '+%Y-%m-%d %H:%M:%S') ====="

MODEL_FILE="/app/models/20260706-151820.tar.gz"
echo "==> Model: $MODEL_FILE ($(stat -c%s "$MODEL_FILE") bytes)"

echo "==> Starting action server on port 5055..."
cd /app
rasa run actions --actions actions --port 5055 &
sleep 5

echo "==> Starting Rasa server on port 7860..."
rasa run -m "$MODEL_FILE" --enable-api --cors "*" --port 7860
