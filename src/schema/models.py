from enum import StrEnum, auto
from typing import TypeAlias


class Provider(StrEnum):
    OPENAI = auto()
    OPENAI_COMPATIBLE = auto()
    AZURE_OPENAI = auto()
    DEEPSEEK = auto()
    ANTHROPIC = auto()
    GOOGLE = auto()
    VERTEXAI = auto()
    GROQ = auto()
    AWS = auto()
    OLLAMA = auto()
    OPENROUTER = auto()
    FAKE = auto()


class OpenAIModelName(StrEnum):
    """https://platform.openai.com/docs/models/gpt-4o"""

    GPT_5_NANO = "gpt-5-nano"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_1 = "gpt-5.1"


class AzureOpenAIModelName(StrEnum):
    """Azure OpenAI model names"""

    AZURE_GPT_4O = "azure-gpt-4o"
    AZURE_GPT_4O_MINI = "azure-gpt-4o-mini"


class OpenAIEmbeddingModelName(StrEnum):
    """https://platform.openai.com/docs/guides/embeddings"""

    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"


class DeepseekModelName(StrEnum):
    """https://api-docs.deepseek.com/quick_start/pricing"""

    DEEPSEEK_CHAT = "deepseek-chat"


class AnthropicModelName(StrEnum):
    """https://docs.anthropic.com/en/docs/about-claude/models#model-names"""

    HAIKU_45 = "claude-haiku-4-5"
    SONNET_45 = "claude-sonnet-4-5"


class GoogleModelName(StrEnum):
    """https://ai.google.dev/gemini-api/docs/models/gemini"""

    GEMINI_15_PRO = "gemini-1.5-pro"
    GEMINI_20_FLASH = "gemini-2.0-flash"
    GEMINI_20_FLASH_LITE = "gemini-2.0-flash-lite"
    GEMINI_25_FLASH = "gemini-2.5-flash"
    GEMINI_25_PRO = "gemini-2.5-pro"
    GEMINI_30_PRO = "gemini-3-pro-preview"


class GoogleEmbeddingModelName(StrEnum):
    """https://ai.google.dev/gemini-api/docs/models/gemini#text-embedding"""

    TEXT_EMBEDDING_004 = "text-embedding-004"


class VertexAIModelName(StrEnum):
    """https://cloud.google.com/vertex-ai/generative-ai/docs/models"""

    GEMINI_15_PRO = "gemini-1.5-pro"
    GEMINI_20_FLASH = "gemini-2.0-flash"
    GEMINI_20_FLASH_LITE = "models/gemini-2.0-flash-lite"
    GEMINI_25_FLASH = "models/gemini-2.5-flash"
    GEMINI_25_PRO = "gemini-2.5-pro"
    GEMINI_30_PRO = "gemini-3-pro-preview"


class GroqModelName(StrEnum):
    """https://console.groq.com/docs/models"""

    LLAMA_GUARD_4_12B = "meta-llama/llama-guard-4-12b"
    LLAMA_31_8B_INSTANT = "llama-3.1-8b-instant"
    LLAMA_33_70B_VERSATILE = "llama-3.3-70b-versatile"
    LLAMA_4_MAVERICK_17B_128E = "meta-llama/llama-4-maverick-17b-128e-instruct"
    LLAMA_4_SCOUT_17B_16E = "meta-llama/llama-4-scout-17b-16e-instruct"
    LLAMA_PROMPT_GUARD_2_22M = "meta-llama/llama-prompt-guard-2-22m"
    LLAMA_PROMPT_GUARD_2_86M = "meta-llama/llama-prompt-guard-2-86m"
    OPENAI_GPT_OSS_120B = "openai/gpt-oss-120b"
    OPENAI_GPT_OSS_20B = "openai/gpt-oss-20b"
    OPENAI_GPT_OSS_SAFEGUARD_20B = "openai/gpt-oss-safeguard-20b"
    GROQ_COMPOUND = "groq/compound"
    GROQ_COMPOUND_MINI = "groq/compound-mini"
    QWEN_3_32B = "qwen/qwen3-32b"
    KIMI_K2_INSTRUCT = "moonshotai/kimi-k2-instruct"
    KIMI_K2_INSTRUCT_0905 = "moonshotai/kimi-k2-instruct-0905"
    ORPHEUS_ARABIC_SAUDI = "canopylabs/orpheus-arabic-saudi"
    ORPHEUS_V1_ENGLISH = "canopylabs/orpheus-v1-english"
    WHISPER_LARGE_V3 = "whisper-large-v3"
    WHISPER_LARGE_V3_TURBO = "whisper-large-v3-turbo"
    ALLAM_2_7B = "allam-2-7b"

class AWSModelName(StrEnum):
    """https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html"""

    BEDROCK_HAIKU = "bedrock-3.5-haiku"
    BEDROCK_SONNET = "bedrock-3.5-sonnet"


class OllamaModelName(StrEnum):
    """https://ollama.com/search"""

    OLLAMA_GENERIC = "ollama"


class OllamaEmbeddingModelName(StrEnum):
    """Common Ollama embedding models"""

    NOMIC_EMBED_TEXT = "nomic-embed-text"
    ALL_MINILM = "all-minilm"


class OpenRouterModelName(StrEnum):
    """https://openrouter.ai/models"""

    GEMINI_25_FLASH = "google/gemini-2.5-flash"


class OpenAICompatibleName(StrEnum):
    """https://platform.openai.com/docs/guides/text-generation"""

    OPENAI_COMPATIBLE = "openai-compatible"


class FakeModelName(StrEnum):
    """Fake model for testing."""

    FAKE = "fake"


AllModelEnum: TypeAlias = (
    OpenAIModelName
    | OpenAICompatibleName
    | AzureOpenAIModelName
    | DeepseekModelName
    | AnthropicModelName
    | GoogleModelName
    | VertexAIModelName
    | GroqModelName
    | AWSModelName
    | OllamaModelName
    | OpenRouterModelName
    | FakeModelName
)

AllEmbeddingModelEnum: TypeAlias = (
    OpenAIEmbeddingModelName
    | GoogleEmbeddingModelName
    | OllamaEmbeddingModelName
)
