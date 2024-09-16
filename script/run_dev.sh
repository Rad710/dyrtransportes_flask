#!/bin/bash
set -e
pid=$!

mypy --install-types
mypy src/

# flask --app app/app.py db upgrade
alembic -c src/migrations/alembic.ini upgrade head

# flask --app src/app.py run --host 0.0.0.0 --port 8080 --debug

flask --app src/app.py run --host 0.0.0.0 --port 8080 --debug