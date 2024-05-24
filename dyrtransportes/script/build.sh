#!/bin/bash
set -e
pid=$!

mypy --install-types
mypy dyrtransportes/

# flask --app app/app.py db upgrade
alembic -c dyrtransportes/migrations/alembic.ini upgrade head

# flask --app dyrtransportes/app.py run --host 0.0.0.0 --port 8080 --debug

flask --app dyrtransportes/app.py run --host 0.0.0.0 --port 8080 --debug