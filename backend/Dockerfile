# Builder image for FastAPI
FROM python:3.12 AS builder

# Set environment variables
ENV PATH="/app/scripts:${PATH}" \
    PYTHONPATH="${PYTHONPATH}:/app" \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copy the shared pyproject.toml and the backend source code
COPY pyproject.toml .
COPY backend/ ./backend/

# Install uv package manager from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install backend dependencies using uv (the 'backend' extras group)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev -E backend

# Final image
FROM python:3.12-slim AS final
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
# Make any scripts executable (if present)
RUN if [ -d "backend/scripts" ]; then chmod +x backend/scripts/*; fi
CMD ["uvicorn", "backend/app.main:app", "--host", "0.0.0.0", "--port", "8000"]