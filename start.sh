#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py loaddata initial_data.json
python manage.py createsuperuser --noinput || true

exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --timeout 120 auth.wsgi:application