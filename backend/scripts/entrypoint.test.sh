#!/bin/sh
set -e

#echo "Upgrading database..."
#alembic upgrade head

echo "Running tests..."
pytest --maxfail=1 #--disable-warnings -q
coverage run -m pytest tests
coverage report -m