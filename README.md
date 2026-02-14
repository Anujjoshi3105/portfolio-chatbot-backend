---
title: Portfolio Chatbot
emoji: 🧰
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Portfolio Chatbot Backend

A robust, production-grade AI agent service built with **LangGraph**, **FastAPI**, and **Python**. Designed to power an intelligent portfolio assistant, this backend orchestrates multiple specialized agents to answer questions about professional experience, analyze GitHub contributions, and track competitive programming statistics.

## Features

*   **Multi-Agent Architecture**: Orchestrates specialized agents for different domains.
    *   **Portfolio Agent**: An expert on Anuj Joshi's background, skills, projects, and work experience, powered by a curated knowledge base.
    *   **Open Source Agent**: Integrates with GitHub (via MCP) to analyze repositories, summarize contributions, and provide code insights.
    *   **Competitive Programming Agent**: Tracks real-time performance and statistics from platforms like LeetCode and Codeforces.
*   **Advanced Memory System**:
    *   **Short-term Memory**: Manages conversation history using LangGraph checkpointers (Postgres, SQLite, or MongoDB).
    *   **Long-term Memory**: Persists cross-conversation knowledge using a durable store.
*   **Model Agnostic**: Supports a wide range of LLM providers including **OpenAI**, **Anthropic**, **Google Gemini/Vertex AI**, **Groq**, **NVIDIA**, **DeepSeek**, **Azure OpenAI**, and **Ollama**.
*   **Production Ready API**:
    *   RESTful endpoints built with **FastAPI**.
    *   Full streaming support (Server-Sent Events) for real-time responses.
    *   Comprehensive conversation history and thread management.
    *   Built-in feedback collection endpoints.
*   **Observability & Tracing**: First-class integration with **LangSmith** and **LangFuse** for monitoring and debugging agent traces.
*   **Dockerized**: extensive Docker support for easy deployment and scaling.

## Tech Stack

*   **Language**: Python 3.11+
*   **Framework**: FastAPI, Uvicorn
*   **AI orchestration**: LangChain, LangGraph
*   **Database**: PostgreSQL (recommended for production), SQLite (dev), MongoDB
*   **Package Manager**: uv (fast Python package installer)

## Project Structure

```
backend/
├── src/
│   ├── agents/          # Agent definitions and workflows
│   │   ├── agents.py    # Agent registry and loading logic
│   │   ├── portfolio_agent.py
│   │   ├── open_source_agent.py
│   │   └── ...
│   ├── core/            # Core configurations and settings
│   ├── memory/          # Database and checkpoint initialization
│   ├── schema/          # Pydantic models and data schemas
│   ├── service/         # FastAPI application and routes
│   └── run_service.py   # Application entry point
├── .env.example         # Environment variable template
├── pyproject.toml       # Dependencies and project metadata
├── compose.yaml         # Docker Compose configuration
└── Dockerfile           # Docker build instructions
```

## Getting Started

### Prerequisites

*   **Python 3.11+** or **Docker**
*   **Git**
*   API Keys for your preferred LLM provider (e.g., OpenAI, Anthropic, Groq).

### Installation (Local)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Anujjoshi3105/portfolio-chatbot-backend.git
    cd portfolio-chatbot-backend
    ```

2.  **Set up the environment:**
    Create a virtual environment and install dependencies. We recommend using `uv` for speed, but `pip` works too.

    ```bash
    # Using uv (Recommended)
    pip install uv
    uv sync

    # OR using standard pip
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt # generate with uv pip compile... or just install from pyproject.toml
    pip install .  # Install the project in editable mode
    ```

3.  **Configure Environment Variables:**
    Copy `.env.example` to `.env` and fill in your API keys.

    ```bash
    cp .env.example .env
    ```

    **Key Configuration Options:**
    *   `OPENAI_API_KEY`, `GROQ_API_KEY`, etc.: API keys for LLMs.
    *   `DEFAULT_MODEL`: The default model to use (e.g., `gpt-4o`, `llama-3.1-70b-versatile`).
    *   `DATABASE_TYPE`: `postgres` or `sqlite`.
    *   `GITHUB_PAT`: GitHub Personal Access Token (for Open Source Agent).
    *   `LANGSMITH_TRACING`: Set to `true` to enable LangSmith tracing.

### Running the Service

Start the backend server:

```bash
# Run using the python script
python src/run_service.py

# OR using uvicorn directly
uvicorn service:app --host 0.0.0.0 --port 7860 --reload
```

The API will be available at `http://localhost:7860`.
Access the interactive API docs (Swagger UI) at `http://localhost:7860/docs`.

## Docker Deployment

1.  **Build and Run with Docker Compose:**
    ```bash
    docker compose up --build
    ```

    This will start the backend service along with a PostgreSQL database (if configured in `compose.yaml`).

## API Endpoints

The service exposes several key endpoints for interacting with the agents:

### 1. **Invoke Agent**
   - **POST** `/invoke` or `/{agent_id}/invoke`
   - Get a complete response from an agent.
   - **Body:** `{ "message": "Tell me about your projects", "thread_id": "optional-uuid" }`

### 2. **Stream Response**
   - **POST** `/stream` or `/{agent_id}/stream`
   - Stream the agent's reasoning and response token-by-token (SSE).
   - **Body:** `{ "message": "...", "stream_tokens": true }`

### 3. **Chat History**
   - **POST** `/history`
   - Retrieve past messages for a specific thread.

### 4. **Service Info**
   - **GET** `/info`
   - Returns available agents, models, and configuration metadata.

## Contributing

Contributions are welcome! Please perform the following steps:
1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
