# Stage 1: Install dependencies
FROM python:3.12-slim AS builder

ENV UV_COMPILE_BYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime image
FROM python:3.12-slim

ENV UV_COMPILE_BYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOST=0.0.0.0
ENV PORT=7860

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Create user before it's referenced in COPY --chown
RUN useradd -m -u 1000 user

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder --chown=user:user /app/.venv ./.venv

# Copy application code
COPY --chown=user:user app/ ./app/

# Create data directory for persistent storage
RUN mkdir -p /data && chmod 777 /data

USER user

EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/api/v1/health || exit 1

CMD ["uv", "run", "python", "-m", "app.main"]