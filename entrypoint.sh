#!/usr/bin/env bash
set -e

echo "Starting Ollama..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
until curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "Waiting for Ollama..."
    sleep 2
done

echo "Pulling models..."
# Pull models based on environment variables or defaults
OLLAMA_MODEL=${OLLAMA_MODEL:-"qwen3:0.6b-q4_K_M"}
OLLAMA_EMBEDDING_MODEL=${OLLAMA_EMBEDDING_MODEL:-"embeddinggemma:300m"}

echo "Pulling model: $OLLAMA_MODEL"
ollama pull $OLLAMA_MODEL

echo "Pulling embedding model: $OLLAMA_EMBEDDING_MODEL"
ollama pull $OLLAMA_EMBEDDING_MODEL

echo "Ollama ready."

echo "Starting Backend Service on port 7860..."
# Set variables for the python service
export HOST=0.0.0.0
export PORT=7860
export OLLAMA_BASE_URL=http://localhost:11434

# Ensure logs are visible
export PYTHONUNBUFFERED=1

# Start the python service
uv run python run_service.py
