#!/bin/sh
# Applies pending Alembic migrations, then starts the app server. Runs on
# every container start - a no-op when the schema is already current.
set -e

flask db upgrade

exec gunicorn --bind 0.0.0.0:5000 --workers 2 wsgi:app
