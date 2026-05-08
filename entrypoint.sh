#!/bin/bash
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 backend.wsgi:application
