# Stage 1: Get the official Ollama binary
FROM ollama/ollama:latest AS ollama_source

# Stage 2: Final Image
FROM python:3.12.3-slim

# Install system dependencies (curl for health, socat for port mapping)
RUN apt-get update && apt-get install -y \
    curl \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Copy Ollama from the official image
COPY --from=ollama_source /usr/bin/ollama /usr/bin/ollama
# Also copy the libraries which are necessary for Ollama to run
COPY --from=ollama_source /usr/lib/ollama /usr/lib/ollama

# Set up the non-root user
RUN useradd -m -u 1000 user
WORKDIR /app
RUN chown user:user /app

# Install uv and dependencies
RUN pip install --no-cache-dir uv

USER user
COPY --chown=user:user pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy app code
COPY --chown=user:user src/agents/ ./agents/
COPY --chown=user:user src/core/ ./core/
COPY --chown=user:user src/memory/ ./memory/
COPY --chown=user:user src/schema/ ./schema/
COPY --chown=user:user src/service/ ./service/
COPY --chown=user:user src/scripts/ ./scripts/
COPY --chown=user:user src/run_service.py ./run_service.py
COPY --chown=user:user entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Environment variables
ENV HOST=0.0.0.0
ENV PORT=7860
ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_KEEP_ALIVE=24h
ENV OLLAMA_BASE_URL=http://localhost:11434

EXPOSE 7860
EXPOSE 11434

RUN mkdir -p /home/user/.ollama
VOLUME ["/home/user/.ollama"]

CMD ["./entrypoint.sh"]
