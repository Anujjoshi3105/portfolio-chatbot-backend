---
title: HF Spaces Chatbot Backend
emoji: 🤖
colorFrom: #6670f8
colorTo: #7c3aed
sdk: gradio
sdk_version: "5.24.0"
app_file: app/main.py
pinned: false
---

# Hugging Face Spaces Chatbot Backend

A production-ready, self-hostable chatbot backend deployed on Hugging Face Spaces.

## Overview

This is an API-first application that provides persistent chatbot functionality, file storage, and RAG document intelligence for multiple frontends including React, Next.js, Flutter, and custom interfaces.

## Features

- **AI Chatbot Conversations** with conversation context
- **Persistent Conversation History** stored in SQLite/PostgreSQL
- **File Upload/Download** with validation and user isolation
- **User-Specific File Management** with namespace separation
- **Document Indexing & RAG**: PDF, DOCX, TXT, Markdown, CSV, JSON, images
- **Streaming AI Responses** via Server-Sent Events (SSE)
- **Multiple LLM Providers**: NVIDIA NIM, OpenAI-compatible, Ollama
- **Persistent Storage** via Hugging Face Storage Buckets
- **API Key Authentication** with isolated user namespaces
- **Swagger/OpenAPI Docs**: `/api/v1/docs` and `/api/v1/redoc`

## Technology Stack

- Python 3.11+
- FastAPI
- SQLAlchemy (SQLite/PostgreSQL compatible)
- Alembic for database migrations
- Hugging Face Storage Buckets for persistent file storage
- ChromaDB for vector storage / document retrieval
- Pydantic v2 for data validation
- uv package manager

## Quick Start

### 1. Clone and setup

```bash
git clone <your-repo>
cd backend
cp .env.example .env
```

### 2. Configure environment variables

Edit `.env` with your settings:

```env
# Required
NVIDIA_API_KEY=nvapi-your-key-here

# Storage - configure one
# Option A: Hugging Face Storage Bucket
HF_STORAGE_BUCKET_NAME=my-chatbot-bucket

# Option B: Local fallback
STORAGE_BASE_PATH=/data

# Optional: OpenAI-compatible provider
# COMPATIBLE_API_KEY=sk-your-key
# COMPATIBLE_BASE_URL=https://api.openai.com/v1

# Database
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=sqlite.db

# Server
HOST=0.0.0.0
PORT=7860
LOG_LEVEL=INFO

# Security
RATE_LIMIT_PER_MINUTE=60
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Limits
MAX_UPLOAD_SIZE=10485760
ALLOWED_FILE_TYPES=pdf,docx,txt,md,csv,json,jpg,jpeg,png,webp
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Initialize the database

```bash
uv run alembic init migrations
uv run alembic upgrade head
```

### 5. Run the server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 7860
```

## Hugging Face Spaces Deployment

### Docker-based Deployment

```bash
docker build -t your-username/chatbot-backend .
docker run -p 7860:7860 \
  -e NVIDIA_API_KEY=$NVIDIA_API_KEY \
  -e HF_STORAGE_BUCKET_NAME=$HF_STORAGE_BUCKET_NAME \
  -e DATABASE_TYPE=$DATABASE_TYPE \
  your-username/chatbot-backend
```

### Space Configuration

1. Create a new Hugging Face Space
2. Select "Docker" as the runtime
3. Set environment variables in Space settings:
   - `NVIDIA_API_KEY` (Secret var)
   - `HF_STORAGE_BUCKET_NAME` (Environment var)
   - `DATABASE_TYPE` (Environment var)
   - `LLM_PROVIDER` (Environment var, default: nvidia)
   - `CORS_ORIGINS` (Environment var)
   - And others as needed

### Storage Bucket Setup

1. Create a storage bucket in your HF Space settings
2. Set `HF_STORAGE_BUCKET_NAME` in environment variables
3. Bucket mounted at `/data/<bucket_name>/`
4. All uploaded files persist across restarts

If no `HF_STORAGE_BUCKET_NAME` is set, falls back to local storage at `STORAGE_BASE_PATH`.

## API Documentation

Once running, access:

- **Swagger UI**: `http://your-space-url/api/v1/docs`
- **ReDoc**: `http://your-space-url/api/v1/redoc`
- **OpenAPI JSON**: `http://your-space-url/api/v1/openapi.json`

### Key Endpoints

#### Chat

```
POST /api/v1/chat/completions
- conversation_id: Optional existing conversation
- message: User message content
- model: Model name (optional)
- provider: LLM provider (optional)
- streaming: Enable SSE (optional, default: false)
- api_key: API key for authentication (query)
```

#### Conversations

```
GET /api/v1/conversations      - List user conversations
POST /api/v1/conversations     - Create new conversation
GET /api/v1/conversations/{id} - Retrieve conversation + messages
DELETE /api/v1/conversations/{id} - Delete conversation
```

#### Files

```
POST /api/v1/files/upload      - Upload files (multipart)
GET /api/v1/files              - List files with pagination
GET /api/v1/files/{file_id}    - File metadata
GET /api/v1/files/{file_id}/download - Download file
DELETE /api/v1/files/{file_id} - Delete file
GET /api/v1/files/{file_id}/status - Processing status
```

## RAG Document Intelligence

1. Upload supported documents (PDF, DOCX, TXT, Markdown, CSV, JSON, images)
2. File validated and stored in persistent storage
3. Text extracted and split into chunks
4. Embeddings generated via configured LLM provider
5. Vectors stored in ChromaDB
6. Documents become searchable via vector similarity
7. During chat, relevant chunks retrieved as context
8. Source citations included in assistant responses

### Supported File Types

- **Documents**: PDF, DOCX, TXT, Markdown (.md), CSV, JSON
- **Images**: JPG, JPEG, PNG, WebP
- **Archives**: ZIP (pass-through)

## Security

- API Key authentication with SHA-256 hashing
- User-isolated namespaces
- MIME type and extension validation
- Configurable upload size limits (default: 10MB)
- CORS origins configuration
- Rate limiting configuration
- Path traversal prevention

## Development

```bash
# Run tests
uv run pytest

# Linting
uv run ruff check
uv run ruff format

# Type checking
uv run mypy app/
```

## License

MIT