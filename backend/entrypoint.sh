#!/bin/sh
set -eu

flask --app run:app db upgrade
exec gunicorn --bind "0.0.0.0:${PORT:-5000}" --workers "${WEB_CONCURRENCY:-2}" run:app
