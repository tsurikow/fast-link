#!/bin/sh
set -e

#echo "Upgrading database..."
#alembic upgrade head

echo "Running tests..."
pytest --maxfail=1 --disable-warnings -q --html=/app/reports/pytest.html
coverage run -m pytest tests
coverage report -m
coverage html -d /app/reports/coverage_html