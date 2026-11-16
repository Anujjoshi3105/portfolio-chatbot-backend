# Stage 1: Install dependencies
FROM python:3.12.3-slim AS builder

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
FROM python:3.12.3-slim

ENV UV_COMPILE_BYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOST=0.0.0.0
ENV PORT=7860

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv \
    && useradd -m -u 1000 user

WORKDIR /app
RUN chown user:user /app

COPY --from=builder --chown=user:user /app/.venv ./.venv
COPY --chown=user:user src/agents/ ./agents/
COPY --chown=user:user src/core/ ./core/
COPY --chown=user:user src/memory/ ./memory/
COPY --chown=user:user src/schema/ ./schema/
COPY --chown=user:user src/service/ ./service/
COPY --chown=user:user src/scripts/ ./scripts/
COPY --chown=user:user src/run_service.py ./run_service.py
USER user

EXPOSE 7860

CMD ["uv", "run", "python", "run_service.py"]
