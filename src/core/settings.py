import logging
import urllib.request
from enum import StrEnum
from json import loads
from typing import Annotated, Any

from dotenv import find_dotenv
from pydantic import (
    BeforeValidator,
    Field,
    HttpUrl,
    SecretStr,
    TypeAdapter,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from schema.models import (
    AllEmbeddingModelEnum,
    AnthropicModelName,
    AWSModelName,
    AzureOpenAIModelName,
    DeepseekModelName,
    FakeModelName,
    GoogleEmbeddingModelName,
    GoogleModelName,
    GroqModelName,
    NvidiaEmbeddingModelName,
    NvidiaModelName,
    OllamaEmbeddingModelName,
    OllamaModelName,
    OpenAICompatibleName,
    OpenAIEmbeddingModelName,
    OpenAIModelName,
    OpenRouterModelName,
    Provider,
    VertexAIModelName,
)

logger = logging.getLogger(__name__)


class DatabaseType(StrEnum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    MONGO = "mongo"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def to_logging_level(self) -> int:
        """Convert to Python logging level constant."""
        import logging

        mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }
        return mapping[self]


def check_str_is_http(x: str) -> str:
    http_url_adapter = TypeAdapter(HttpUrl)
    return str(http_url_adapter.validate_python(x))


def _fetch_json_get(url: str, api_key: str | None, timeout: float = 15.0) -> list[str]:
    """GET a JSON endpoint and return ``data[].id`` (OpenAI-style list) or ``models[].name`` (Ollama)."""
    if not api_key:
        return []
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = loads(response.read().decode("utf-8"))
    except Exception:
        return []
    items = data.get("data") or data.get("models") or []
    ids: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        mid = item.get("id") or item.get("name")
        if mid:
            ids.append(str(mid))
    return ids


def _fetch_ollama_models(base_url: str | None) -> list[str]:
    if not base_url:
        return []
    url = base_url.rstrip("/") + "/api/tags"
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15.0) as response:
            data = loads(response.read().decode("utf-8"))
    except Exception:
        return []
    ids: list[str] = []
    for item in data.get("models", []) or []:
        if isinstance(item, dict) and item.get("name"):
            ids.append(str(item["name"]))
    return ids


def _fetch_live_models(provider: Provider, api_key: str | None, base_url: str | None) -> list[str]:
    """Return live model ids for a provider, or an empty list if the API is unreachable."""
    match provider:
        case Provider.OPENAI:
            return _fetch_json_get("https://api.openai.com/v1/models", api_key)
        case Provider.DEEPSEEK:
            return _fetch_json_get("https://api.deepseek.com/v1/models", api_key)
        case Provider.GROQ:
            return _fetch_json_get("https://api.groq.com/openai/v1/models", api_key)
        case Provider.OPENROUTER:
            return _fetch_json_get("https://openrouter.ai/api/v1/models", api_key)
        case Provider.NVIDIA:
            return _fetch_json_get("https://integrate.api.nvidia.com/v1/models", api_key)
        case Provider.OLLAMA:
            return _fetch_ollama_models(base_url)
        case (
            Provider.ANTHROPIC
            | Provider.GOOGLE
            | Provider.VERTEXAI
            | Provider.AWS
            | Provider.AZURE_OPENAI
            | Provider.OPENAI_COMPATIBLE
            | Provider.FAKE
        ):
            # No public model-list endpoint; rely on the bundled enum instead.
            return []
        case _:
            return []


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        validate_default=False,
    )
    MODE: str | None = None

    HOST: str = "0.0.0.0"
    PORT: int = 7860
    GRACEFUL_SHUTDOWN_TIMEOUT: int = 30
    LOG_LEVEL: LogLevel = LogLevel.WARNING

    AUTH_SECRET: SecretStr | None = None
    CORS_ORIGINS: Annotated[
        Any, BeforeValidator(lambda x: x.split(",") if isinstance(x, str) else x)
    ] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    OPENAI_API_KEY: SecretStr | None = None
    DEEPSEEK_API_KEY: SecretStr | None = None
    ANTHROPIC_API_KEY: SecretStr | None = None
    GOOGLE_API_KEY: SecretStr | None = None
    GOOGLE_APPLICATION_CREDENTIALS: SecretStr | None = None
    GROQ_API_KEY: SecretStr | None = None
    USE_AWS_BEDROCK: bool = False
    OLLAMA_MODEL: str | None = None
    OLLAMA_EMBEDDING_MODEL: str | None = None
    OLLAMA_BASE_URL: str | None = None
    USE_FAKE_MODEL: bool = False
    OPENROUTER_API_KEY: str | None = None
    NVIDIA_API_KEY: SecretStr | None = None

    # If DEFAULT_MODEL is None, it will be set in model_post_init
    DEFAULT_MODEL: str | None = None  # type: ignore[assignment]
    AVAILABLE_MODELS: set[str] = set()  # type: ignore[assignment]
    # model id -> provider, used by core/llm.py to route instantiation
    MODEL_PROVIDER_MAP: dict[str, Provider] = Field(default_factory=dict)

    # Embedding Settings
    DEFAULT_EMBEDDING_MODEL: AllEmbeddingModelEnum | None = None  # type: ignore[assignment]
    AVAILABLE_EMBEDDING_MODELS: set[AllEmbeddingModelEnum] = set()  # type: ignore[assignment]

    # Set openai compatible api, mainly used for proof of concept
    COMPATIBLE_MODEL: str | None = None
    COMPATIBLE_API_KEY: SecretStr | None = None
    COMPATIBLE_BASE_URL: str | None = None

    OPENWEATHERMAP_API_KEY: SecretStr | None = None

    CONTEST_API_URL: str | None = None

    # MCP Configuration
    GITHUB_PAT: SecretStr | None = None
    MCP_GITHUB_SERVER_URL: str = "https://api.githubcopilot.com/mcp/"

    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_PROJECT: str = "default"
    LANGCHAIN_ENDPOINT: Annotated[str, BeforeValidator(check_str_is_http)] = (
        "https://api.smith.langchain.com"
    )
    LANGCHAIN_API_KEY: SecretStr | None = None

    LANGFUSE_TRACING: bool = False
    LANGFUSE_HOST: Annotated[str, BeforeValidator(check_str_is_http)] = "https://cloud.langfuse.com"
    LANGFUSE_PUBLIC_KEY: SecretStr | None = None
    LANGFUSE_SECRET_KEY: SecretStr | None = None

    # Safety Guard Configuration
    ENABLE_SAFETY_GUARD: bool = True

    # Database Configuration
    DATABASE_TYPE: DatabaseType = (
        DatabaseType.SQLITE
    )  # Options: DatabaseType.SQLITE or DatabaseType.POSTGRES
    SQLITE_DB_PATH: str = "checkpoints.db"

    # PostgreSQL Configuration
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_APPLICATION_NAME: str = "chatbot"
    POSTGRES_MIN_CONNECTIONS_PER_POOL: int = 1
    POSTGRES_MAX_CONNECTIONS_PER_POOL: int = 1
    VECTOR_STORE_COLLECTION_NAME: str = "vector_store"

    # MongoDB Configuration
    MONGO_HOST: str | None = None
    MONGO_PORT: int | None = None
    MONGO_DB: str | None = None
    MONGO_USER: str | None = None
    MONGO_PASSWORD: SecretStr | None = None
    MONGO_AUTH_SOURCE: str | None = None
    MONGO_TLS: bool = False

    # Optional voice providers. Voice is disabled unless a provider is selected.
    VOICE_STT_PROVIDER: str | None = None
    VOICE_TTS_PROVIDER: str | None = None
    VOICE_MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024
    DEEPGRAM_API_KEY: SecretStr | None = None
    ELEVENLABS_API_KEY: SecretStr | None = None

    # Azure OpenAI Settings
    AZURE_OPENAI_API_KEY: SecretStr | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT_MAP: dict[str, str] = Field(
        default_factory=dict, description="Map of model names to Azure deployment IDs"
    )

    def model_post_init(self, __context: Any) -> None:
        api_keys = {
            Provider.OPENAI: self.OPENAI_API_KEY,
            Provider.OPENAI_COMPATIBLE: self.COMPATIBLE_BASE_URL and self.COMPATIBLE_MODEL,
            Provider.DEEPSEEK: self.DEEPSEEK_API_KEY,
            Provider.ANTHROPIC: self.ANTHROPIC_API_KEY,
            Provider.GOOGLE: self.GOOGLE_API_KEY,
            Provider.VERTEXAI: self.GOOGLE_APPLICATION_CREDENTIALS,
            Provider.GROQ: self.GROQ_API_KEY,
            Provider.AWS: self.USE_AWS_BEDROCK,
            Provider.OLLAMA: self.OLLAMA_MODEL,
            Provider.FAKE: self.USE_FAKE_MODEL,
            Provider.AZURE_OPENAI: self.AZURE_OPENAI_API_KEY,
            Provider.OPENROUTER: self.OPENROUTER_API_KEY,
            Provider.NVIDIA: self.NVIDIA_API_KEY,
        }
        active_keys = [k for k, v in api_keys.items() if v]
        if not active_keys:
            raise ValueError("At least one LLM API key must be provided.")

        # Bundled enum fallback values per provider (value, default)
        _BUNDLED: dict[Provider, tuple[list[str], str]] = {
            Provider.OPENAI: (
                [m.value for m in OpenAIModelName],
                OpenAIModelName.GPT_5_NANO.value,
            ),
            Provider.OPENAI_COMPATIBLE: (
                [m.value for m in OpenAICompatibleName],
                OpenAICompatibleName.OPENAI_COMPATIBLE.value,
            ),
            Provider.DEEPSEEK: (
                [m.value for m in DeepseekModelName],
                DeepseekModelName.DEEPSEEK_CHAT.value,
            ),
            Provider.ANTHROPIC: (
                [m.value for m in AnthropicModelName],
                AnthropicModelName.HAIKU_45.value,
            ),
            Provider.GOOGLE: (
                [m.value for m in GoogleModelName],
                GoogleModelName.GEMINI_20_FLASH.value,
            ),
            Provider.VERTEXAI: (
                [m.value for m in VertexAIModelName],
                VertexAIModelName.GEMINI_20_FLASH.value,
            ),
            Provider.NVIDIA: (
                [m.value for m in NvidiaModelName],
                NvidiaModelName.NVIDIA_LLAMA_3_1_NEMOTRON_70B_INSTRUCT.value,
            ),
            Provider.GROQ: (
                [m.value for m in GroqModelName],
                GroqModelName.GROQ_COMPOUND_MINI.value,
            ),
            Provider.AWS: (
                [m.value for m in AWSModelName],
                AWSModelName.BEDROCK_HAIKU.value,
            ),
            Provider.OLLAMA: (
                [m.value for m in OllamaModelName],
                OllamaModelName.OLLAMA_GENERIC.value,
            ),
            Provider.OPENROUTER: (
                [m.value for m in OpenRouterModelName],
                OpenRouterModelName.GEMINI_25_FLASH.value,
            ),
            Provider.FAKE: (
                [m.value for m in FakeModelName],
                FakeModelName.FAKE.value,
            ),
            Provider.AZURE_OPENAI: (
                [m.value for m in AzureOpenAIModelName],
                AzureOpenAIModelName.AZURE_GPT_4O_MINI.value,
            ),
        }

        for provider in active_keys:
            bundled_models, bundled_default = _BUNDLED[provider]
            api_key = api_keys[provider]
            # Resolve the api_key/secret to a raw string for live fetching.
            key_str = (
                api_key.get_secret_value() if hasattr(api_key, "get_secret_value") else api_key
            )
            base_url = (
                self.COMPATIBLE_BASE_URL
                if provider == Provider.OPENAI_COMPATIBLE
                else self.OLLAMA_BASE_URL
            )

            live_models = _fetch_live_models(provider, key_str, base_url)
            models = (
                list(dict.fromkeys(bundled_models + live_models))
                if live_models
                else bundled_models
            )
            source = "live API + bundled enum" if live_models else "bundled enum"

            self.AVAILABLE_MODELS.update(models)
            for mid in models:
                self.MODEL_PROVIDER_MAP[mid] = provider

            if self.DEFAULT_MODEL is None:
                self.DEFAULT_MODEL = models[0]
                logger.info(f"Default model for {provider} set to {self.DEFAULT_MODEL} ({source})")

        # Azure OpenAI requires explicit deployment configuration (no public model list).
        if Provider.AZURE_OPENAI in active_keys:
            if not self.AZURE_OPENAI_API_KEY:
                raise ValueError("AZURE_OPENAI_API_KEY must be set")
            if not self.AZURE_OPENAI_ENDPOINT:
                raise ValueError("AZURE_OPENAI_ENDPOINT must be set")
            if not self.AZURE_OPENAI_DEPLOYMENT_MAP:
                raise ValueError("AZURE_OPENAI_DEPLOYMENT_MAP must be set")
            if isinstance(self.AZURE_OPENAI_DEPLOYMENT_MAP, str):
                try:
                    self.AZURE_OPENAI_DEPLOYMENT_MAP = loads(self.AZURE_OPENAI_DEPLOYMENT_MAP)
                except Exception as e:
                    raise ValueError(f"Invalid AZURE_OPENAI_DEPLOYMENT_MAP JSON: {e}")
            required_models = {"gpt-4o", "gpt-4o-mini"}
            missing_models = required_models - set(self.AZURE_OPENAI_DEPLOYMENT_MAP.keys())
            if missing_models:
                raise ValueError(f"Missing required Azure deployments: {missing_models}")

        for provider in active_keys:
            match provider:
                case Provider.OPENAI:
                    if self.DEFAULT_EMBEDDING_MODEL is None:
                        self.DEFAULT_EMBEDDING_MODEL = (
                            OpenAIEmbeddingModelName.TEXT_EMBEDDING_3_SMALL
                        )
                    self.AVAILABLE_EMBEDDING_MODELS.update(set(OpenAIEmbeddingModelName))
                case Provider.GOOGLE:
                    if self.DEFAULT_EMBEDDING_MODEL is None:
                        self.DEFAULT_EMBEDDING_MODEL = GoogleEmbeddingModelName.TEXT_EMBEDDING_004
                    self.AVAILABLE_EMBEDDING_MODELS.update(set(GoogleEmbeddingModelName))
                case Provider.OLLAMA:
                    if self.DEFAULT_EMBEDDING_MODEL is None:
                        self.DEFAULT_EMBEDDING_MODEL = OllamaEmbeddingModelName.NOMIC_EMBED_TEXT
                    self.AVAILABLE_EMBEDDING_MODELS.update(set(OllamaEmbeddingModelName))
                    if not self.OLLAMA_EMBEDDING_MODEL:
                        self.OLLAMA_EMBEDDING_MODEL = OllamaEmbeddingModelName.NOMIC_EMBED_TEXT
                case Provider.NVIDIA:
                    if self.DEFAULT_EMBEDDING_MODEL is None:
                        self.DEFAULT_EMBEDDING_MODEL = (
                            NvidiaEmbeddingModelName.NV_EMBEDQA_MISTRAL_7B_V2
                        )
                    self.AVAILABLE_EMBEDDING_MODELS.update(set(NvidiaEmbeddingModelName))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def BASE_URL(self) -> str:
        return f"http://{self.HOST}:{self.PORT}"

    def is_dev(self) -> bool:
        return self.MODE == "dev"


settings = Settings()
