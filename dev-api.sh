#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export DB_DSN="postgresql://postgres.tbhtwbiopenrqjrurewg:qbc7fmjyvu9qwm5JQT@aws-1-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require"

# Force real DB stream only (don’t export the whole .env!)
export OCULUS_STREAM_SOURCE="db"
export MOCK_EVENTS_ENABLED="false"

# Provide DB_DSN only; leave the rest to pydantic’s DotEnv loader in main.py
: "${DB_DSN:=${DATABASE_URL:-${SUPABASE_DB_URL:-}}}"
if [[ -z "${DB_DSN}" ]]; then
  echo "ERROR: DB_DSN is not set. Set DB_DSN (or SUPABASE_DB_URL/DATABASE_URL) in .env or export it here."
  exit 1
fi
export DB_DSN

echo "[LAUNCH] STREAM_SOURCE=${OCULUS_STREAM_SOURCE}"
echo "[LAUNCH] DB_DSN present: YES"
echo "[LAUNCH] Starting FastAPI on :8000"

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
