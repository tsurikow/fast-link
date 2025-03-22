# Builder stage for Streamlit
FROM python:3.12 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy the shared dependency files and the frontend source code
COPY pyproject.toml .
COPY uv.lock* .
COPY frontend/ ./frontend/

# Install uv package manager from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install frontend dependencies using uv (installing the 'frontend' extras group)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev --extra frontend

# Final image
FROM python:3.12-slim AS final
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
# CMD is defined here, but will be overridden by docker-compose if needed.
CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501"]