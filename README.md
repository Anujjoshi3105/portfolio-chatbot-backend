# Hugging Face Spaces Chatbot Backend

A production-ready, self-hostable chatbot backend deployed on Hugging Face Spaces.
This is an API-first application supporting multiple frontends including React, Next.js, Flutter, and custom chatbot interfaces.

## Features

- **AI Chatbot Conversations**: POST `/api/v1/chat/completions` with conversation context
- **Persistent Conversation History**: Stored in SQLite/PostgreSQL, survives restarts
- **File Upload/Download**: Secure file management with validation
- **User-Specific File Management**: Isolated namespaces per user
- **Document Indexing & RAG**: PDF, DOCX, TXT, Markdown, CSV, JSON, image support
- **Streaming AI Responses**: Server-Sent Events (SSE)
- **Multiple LLM Providers**: NVIDIA NIM, OpenAI-compatible, Ollama, etc.
- **Persistent Storage**: Hugging Face Storage Buckets mounted at `/data`
- **API Key Authentication**: Isolated user namespaces
- **Swagger/OpenAPI Docs**: `/docs` and `/redoc`

## Technology Stack

- Python 3.11+
- FastAPI
- SQLAlchemy (SQLite / PostgreSQL compatible)
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

```
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
DATABASE_TYPE=sqlite  # or postgres

# Server
HOST=0.0.0.0
PORT=7860
LOG_LEVEL=INFO

# Security
RATE_LIMIT_PER_MINUTE=60
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Limits
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=pdf,docx,txt,md,csv,json,jpg,jpeg,png,webp
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Initialize the database

```bash
uv run alembic init migrations
# Edit migrations/env.py to use our settings
uv run alembic upgrade head
```

### 5. Run the server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 7860
```

Or with the built-in runner:

```bash
uv run
```

## Hugging Face Spaces Deployment

### Docker-based Deployment

The included Dockerfile builds a production-ready image for Hugging Face Spaces:

```bash
docker build -t your-username/chatbot-backend .
docker run -p 7860:7860 \
  -e NVIDIA_API_KEY=$NVIDIA_API_KEY \
  -e HF_STORAGE_BUCKET_NAME=$HF_STORAGE_BUCKET_NAME \
  -e DATABASE_TYPE=$DATABASE_TYPE \
  your-username/chatbot-backend
```

### HF Spaces Configuration

1. Create a new Hugging Face Space
2. Select "Docker" as the runtime
3. Push your Docker image or use the built image
4. Set the following environment variables in the Space settings:

| Variable | Required | Description |
|---|---|---|
| `NVIDIA_API_KEY` | Yes (for NVIDIA provider) | NVIDIA NIM API key |
| `HF_STORAGE_BUCKET_NAME` | Yes | HF Storage bucket name |
| `DATABASE_TYPE` | Yes | `sqlite` or `postgres` |
| `LLM_PROVIDER` | No | `nvidia` (default) or `openai_compatible` |
| `STORAGE_BASE_PATH` | No | Path for local fallback (`/data`) |
| `CORS_ORIGINS` | No | Comma-separated list of allowed origins |

### Storage Bucket Setup

Hugging Face Storage Buckets provide persistent storage that survives container restarts and rebuilds.

1. Create a storage bucket in your HF Space settings
2. Set `HF_STORAGE_BUCKET_NAME` in environment variables
3. The bucket will be mounted at `/data/<bucket_name>/`
4. All uploaded files and generated artifacts will be persistently stored

If no `HF_STORAGE_BUCKET_NAME` is set, the backend falls back to local storage at the path specified by `STORAGE_BASE_PATH` (default: `./data`).

## API Documentation

Once running, access the following documentation endpoints:

- **Swagger UI**: `http://your-space-url/api/v1/docs`
- **ReDoc**: `http://your-space-url/api/v1/redoc`
- **OpenAPI JSON**: `http://your-space-url/api/v1/openapi.json`

### Key Endpoints

#### Chat

```
POST /api/v1/chat/completions
- conversation_id: Optional existing conversation ID
- message: User message content
- model: Model name (optional, uses default if not specified)
- provider: LLM provider (optional, uses configured default)
- streaming: Enable SSE streaming (optional, default: false)
- api_key: API key for authentication (query parameter)
```

```
GET /api/v1/models
- Returns available models and providers
- Requires api_key query parameter
```

#### Conversations

```
GET /api/v1/conversations
- Lists conversations for authenticated user
- Query: limit, offset

POST /api/v1/conversations
- title: Optional conversation title

GET /api/v1/conversations/{id}
- Retrieves conversation and message history

DELETE /api/v1/conversations/{id}
- Deletes conversation and associated resources

PATCH /api/v1/conversations/{id}
- Update conversation metadata
```

#### Files

```
POST /api/v1/files/upload
- conversation_id: Optional conversation association
- files: Multiple file upload (multipart/form-data)
- Validates file type and size
- Returns file metadata and storage info

GET /api/v1/files
- Lists uploaded files with pagination
- Filters: file_type, conversation_id

GET /api/v1/files/{file_id}
- Returns file metadata

GET /api/v1/files/{file_id}/download
- Downloads the original file

DELETE /api/v1/files/{file_id}
- Deletes file and associated indexed content

GET /api/v1/files/{file_id}/status
- Returns processing and indexing status
```

## RAG Document Intelligence Pipeline

1. Upload a supported document (PDF, DOCX, TXT, Markdown, CSV, JSON, images)
2. File is validated and stored in persistent storage
3. Text is extracted and split into configurable chunks
4. Embeddings are generated using the configured provider
5. Vectors and metadata are stored in ChromaDB
6. Documents become searchable via vector similarity
7. During chat, relevant chunks are retrieved and included as context
8. Source citations are included in assistant responses

### Supported File Types

- **Documents**: PDF, DOCX, TXT, Markdown (.md), CSV, JSON
- **Images**: JPG, JPEG, PNG, WebP
- **Archives**: ZIP (pass-through)

### Chunking Configuration

Default chunk size: 1000 characters
Default chunk overlap: 200 characters
Can be customized via environment variables or API parameters.

## Security

- **API Key Authentication**: Each user gets an isolated namespace
- **Hashing**: API keys are SHA-256 hashed before storage
- **File Validation**: MIME type and extension validation
- **Size Limits**: Configurable maximum upload size (default: 10MB)
- **CORS**: Configurable origins only
- **Rate Limiting**: Configurable per-minute rate limits
- **Ownership Verification**: Users can only access their own data
- **Path Traversal Prevention**: All file paths are sanitized

## Development

### Running Tests

```bash
uv run pytest
```

### Linting

```bash
uv run ruff check
uv run ruff format
```

### Type Checking

```bash
uv run mypy app/
```

### Adding a New LLM Provider

1. Create a new file in `app/providers/` following the `LLMProvider` interface
2. Register the provider in `app/providers/__init__.py`
3. Add environment variables in `.env.example`
4. The chat API will automatically support the new provider

## License

MIT