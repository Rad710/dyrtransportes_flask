#!/bin/bash
set -e
pid=$!

mypy --install-types
mypy app/app.py

flask --app app/app.py db upgrade

flask --app app/app.py run --host 0.0.0.0 --port 8080 --debug