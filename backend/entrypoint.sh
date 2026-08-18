#!/bin/sh
# Applies pending Alembic migrations, then starts the app server. Runs on
# every container start - a no-op when the schema is already current.
set -e

flask db upgrade

exec gunicorn --bind 0.0.0.0:5000 --workers 2 \
    --timeout 30 --graceful-timeout 30 \
    --worker-tmp-dir /dev/shm \
    --access-logfile - --error-logfile - \
    wsgi:app
