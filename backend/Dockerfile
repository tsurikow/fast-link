# Builder stage for FastAPI
FROM python:3.12 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy the shared dependency files and the backend source code
COPY pyproject.toml .
COPY uv.lock* .
COPY alembic.ini .
COPY backend/ ./backend/

# Copy the entrypoint script from the backend/scripts folder
COPY backend/scripts/entrypoint.sh /app/backend/scripts/entrypoint.sh

# Make sure the script is executable
RUN chmod +x /app/backend/scripts/entrypoint.sh

# Install uv package manager from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install backend dependencies using uv (installing the 'backend' extras group)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev --extra backend

# Final image
FROM python:3.12-slim AS final
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
# CMD is defined here, but will be overridden by docker-compose if needed.
CMD ["uvicorn", "backend/app.main:app", "--host", "0.0.0.0", "--port", "8000"]