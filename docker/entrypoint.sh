#!/bin/sh
set -e
# Semaya ve referans tohumlarina (idempotent) — PostgreSQL + Alembic
python -c "from db.init_database import migrate_db; migrate_db()"
exec gunicorn \
  --bind "0.0.0.0:5000" \
  --workers "${GUNICORN_WORKERS:-4}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile "-" \
  --error-logfile "-" \
  "RestApi:app"
