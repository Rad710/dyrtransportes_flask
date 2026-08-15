#!/bin/bash
set -e

# Test database, thrown away with the container
docker compose -f deploy/docker-compose.test.yml up -d --wait

pip install -r requirements-common.txt
pip install -r requirements-dev.txt

pytest "$@"
