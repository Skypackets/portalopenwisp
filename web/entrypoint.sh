#!/usr/bin/env bash
set -euo pipefail

cd /app/web
echo "Waiting for Postgres at ${DATABASE_URL}..."
python - <<'PY'
import os, sys, time
import urllib.parse as up
import socket

db_url = os.environ.get('DATABASE_URL', '')
if not db_url:
    sys.exit(0)

u = up.urlparse(db_url)
host = u.hostname or 'db'
port = int(u.port or 5432)

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            sys.exit(0)
    except OSError:
        time.sleep(1)
print('Database not reachable', file=sys.stderr)
sys.exit(1)
PY

python manage.py collectstatic --noinput
python manage.py migrate --noinput

if [[ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]] && [[ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
  python - <<'PY'
import os
from django.core.management import execute_from_command_line
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
email = os.environ['DJANGO_SUPERUSER_EMAIL']
password = os.environ['DJANGO_SUPERUSER_PASSWORD']
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(username=email, email=email, password=password)
    print('Created superuser', email)
else:
    print('Superuser exists', email)
PY
fi

exec gunicorn portal.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3}

