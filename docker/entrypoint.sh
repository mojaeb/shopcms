#!/bin/sh
set -eu

if [ "${SKIP_ENTRYPOINT_SETUP:-0}" = "1" ]; then
  echo "[entrypoint] SKIP_ENTRYPOINT_SETUP=1 — starting: $*"
  exec "$@"
fi

echo "[entrypoint] waiting for database..."
python - <<'PY'
import os, time
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.staging"))
django.setup()
from django.db import connection
from django.db.utils import OperationalError

for i in range(60):
    try:
        connection.ensure_connection()
        print("[entrypoint] database is ready")
        break
    except OperationalError:
        time.sleep(1)
else:
    raise SystemExit("database not ready")
PY

if [ "${RUN_MIGRATE:-1}" = "1" ]; then
  echo "[entrypoint] migrate..."
  python manage.py migrate --noinput
fi

SEED_DIR="${SEED_DATA_DIR:-/seed}"
MARKER="/app/media/.seed_loaded"

if [ "${LOAD_SEED_DATA:-1}" = "1" ] && [ -f "${SEED_DIR}/data.json" ]; then
  set +e
  python - <<'PY'
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.staging"))
django.setup()
from django.apps import apps
Store = apps.get_model("tenants", "Store")
count = Store.objects.count()
print("[entrypoint] store_count=", count)
raise SystemExit(0 if count else 2)
PY
  status=$?
  set -e
  if [ "$status" -eq 2 ]; then
    echo "[entrypoint] loading seed data from ${SEED_DIR}/data.json ..."
    python manage.py loaddata "${SEED_DIR}/data.json"
  else
    echo "[entrypoint] database already has stores — skip loaddata"
  fi
fi

if [ "${LOAD_SEED_MEDIA:-1}" = "1" ] && [ -d "${SEED_DIR}/media" ] && [ ! -f "$MARKER" ]; then
  echo "[entrypoint] copying seed media..."
  mkdir -p /app/media
  cp -a "${SEED_DIR}/media/." /app/media/ 2>/dev/null || cp -r "${SEED_DIR}/media/." /app/media/
  touch "$MARKER"
  echo "[entrypoint] seed media copied"
elif [ -f "$MARKER" ]; then
  echo "[entrypoint] seed media already present — skip"
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  echo "[entrypoint] collectstatic..."
  python manage.py collectstatic --noinput
fi

echo "[entrypoint] starting: $*"
exec "$@"
