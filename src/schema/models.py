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
    NVIDIA = auto()
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

    #    LLAMA_GUARD_4_12B = "meta-llama/llama-guard-4-12b"
    #    LLAMA_31_8B_INSTANT = "llama-3.1-8b-instant"
    #    LLAMA_33_70B_VERSATILE = "llama-3.3-70b-versatile"
    #    LLAMA_4_MAVERICK_17B_128E = "meta-llama/llama-4-maverick-17b-128e-instruct"
    #    LLAMA_4_SCOUT_17B_16E = "meta-llama/llama-4-scout-17b-16e-instruct"
    LLAMA_PROMPT_GUARD_2_22M = "meta-llama/llama-prompt-guard-2-22m"
    LLAMA_PROMPT_GUARD_2_86M = "meta-llama/llama-prompt-guard-2-86m"
    #    OPENAI_GPT_OSS_120B = "openai/gpt-oss-120b"
    #    OPENAI_GPT_OSS_20B = "openai/gpt-oss-20b"
    OPENAI_GPT_OSS_SAFEGUARD_20B = "openai/gpt-oss-safeguard-20b"
    #    GROQ_COMPOUND = "groq/compound"
    GROQ_COMPOUND_MINI = "groq/compound-mini"
    #    QWEN_3_32B = "qwen/qwen3-32b"
    #    KIMI_K2_INSTRUCT = "moonshotai/kimi-k2-instruct"
    #    KIMI_K2_INSTRUCT_0905 = "moonshotai/kimi-k2-instruct-0905"
    ORPHEUS_ARABIC_SAUDI = "canopylabs/orpheus-arabic-saudi"
    ORPHEUS_V1_ENGLISH = "canopylabs/orpheus-v1-english"
    #    WHISPER_LARGE_V3 = "whisper-large-v3"
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
    EMBEDDING_GEMMA = "embeddinggemma:300m"


class OpenRouterModelName(StrEnum):
    """https://openrouter.ai/models"""

    GEMINI_25_FLASH = "google/gemini-2.5-flash"


class NvidiaModelName(StrEnum):
    """https://build.nvidia.com/explore/discover"""

    #    ABACUSAI_DRACARYS_LLAMA_3_1_70B_INSTRUCT = "abacusai/dracarys-llama-3.1-70b-instruct"
    #    ADEPT_FUYU_8B = "adept/fuyu-8b"
    #    AI21LABS_JAMBA_1_5_LARGE_INSTRUCT = "ai21labs/jamba-1.5-large-instruct"
    #    AI21LABS_JAMBA_1_5_MINI_INSTRUCT = "ai21labs/jamba-1.5-mini-instruct"
    #    AISINGAPORE_SEA_LION_7B_INSTRUCT = "aisingapore/sea-lion-7b-instruct"
    #    BAAI_GET_M3 = "baai/get-m3"
    #    BAICHUAN_INC_BAICHUAN2_13B_CHAT = "baichuan-inc/baichuan2-13b-chat"
    #    BIGCODE_STARCODER2_15B = "bigcode/starcoder2-15b"
    #    BIGCODE_STARCODER2_7B = "bigcode/starcoder2-7b"
    #    BYTEDANCE_SEED_OSS_36B_INSTRUCT = "bytedance/seed-oss-36b-instruct"
    #    DATABRICKS_DBRX_INSTRUCT = "databricks/dbrx-instruct"
    #    DEEPSEEK_AI_DEEPSEEK_CODER_6_7B_INSTRUCT = "deepseek-ai/deepseek-coder-6.7b-instruct"
    #    DEEPSEEK_AI_DEEPSEEK_R1_DISTILL_LLAMA_8B = "deepseek-ai/deepseek-r1-distill-llama-8b"
    #    DEEPSEEK_AI_DEEPSEEK_R1_DISTILL_QWEN_14B = "deepseek-ai/deepseek-r1-distill-qwen-14b"
    #    DEEPSEEK_AI_DEEPSEEK_R1_DISTILL_QWEN_32B = "deepseek-ai/deepseek-r1-distill-qwen-32b"
    #    DEEPSEEK_AI_DEEPSEEK_R1_DISTILL_QWEN_7B = "deepseek-ai/deepseek-r1-distill-qwen-7b"
    #    DEEPSEEK_AI_DEEPSEEK_V3_1 = "deepseek-ai/deepseek-v3.1"
    DEEPSEEK_AI_DEEPSEEK_V3_1_TERMINUS = "deepseek-ai/deepseek-v3.1-terminus"
    DEEPSEEK_AI_DEEPSEEK_V3_2 = "deepseek-ai/deepseek-v3.2"
    GOOGLE_CODEGEMMA_1_1_7B = "google/codegemma-1.1-7b"
    GOOGLE_CODEGEMMA_7B = "google/codegemma-7b"
    GOOGLE_DEPLOT = "google/deplot"
    GOOGLE_GEMMA_2B = "google/gemma-2b"
    GOOGLE_GEMMA_2_27B_IT = "google/gemma-2-27b-it"
    GOOGLE_GEMMA_2_2B_IT = "google/gemma-2-2b-it"
    GOOGLE_GEMMA_2_9B_IT = "google/gemma-2-9b-it"
    GOOGLE_GEMMA_3N_E2B_IT = "google/gemma-3n-e2b-it"
    GOOGLE_GEMMA_3N_E4B_IT = "google/gemma-3n-e4b-it"
    GOOGLE_GEMMA_3_12B_IT = "google/gemma-3-12b-it"
    GOOGLE_GEMMA_3_1B_IT = "google/gemma-3-1b-it"
    GOOGLE_GEMMA_3_27B_IT = "google/gemma-3-27b-it"
    GOOGLE_GEMMA_3_4B_IT = "google/gemma-3-4b-it"
    GOOGLE_GEMMA_7B = "google/gemma-7b"
    GOOGLE_PALIGEMMA = "google/paligemma"
    GOOGLE_RECURRENTGEMMA_2B = "google/recurrentgemma-2b"
    GOOGLE_SHIELDGEMMA_9B = "google/shieldgemma-9b"
    GOTOCOMPANY_GEMMA_2_9B_CPT_SAHABATAI_INSTRUCT = "gotocompany/gemma-2-9b-cpt-sahabatai-instruct"
    IBM_GRANITE_34B_CODE_INSTRUCT = "ibm/granite-34b-code-instruct"
    IBM_GRANITE_3_0_3B_A800M_INSTRUCT = "ibm/granite-3.0-3b-a800m-instruct"
    IBM_GRANITE_3_0_8B_INSTRUCT = "ibm/granite-3.0-8b-instruct"
    IBM_GRANITE_3_3_8B_INSTRUCT = "ibm/granite-3.3-8b-instruct"
    IBM_GRANITE_8B_CODE_INSTRUCT = "ibm/granite-8b-code-instruct"
    IBM_GRANITE_GUARDIAN_3_0_8B = "ibm/granite-guardian-3.0-8b"
    IGENIUS_COLOSSEUM_355B_INSTRUCT_16K = "igenius/colosseum_355b_instruct_16k"
    IGENIUS_ITALIA_10B_INSTRUCT_16K = "igenius/italia_10b_instruct_16k"
    INSTITUTE_OF_SCIENCE_TOKYO_LLAMA_3_1_SWALLOW_70B_INSTRUCT_V0_1 = (
        "institute-of-science-tokyo/llama-3.1-swallow-70b-instruct-v0.1"
    )
    INSTITUTE_OF_SCIENCE_TOKYO_LLAMA_3_1_SWALLOW_8B_INSTRUCT_V0_1 = (
        "institute-of-science-tokyo/llama-3.1-swallow-8b-instruct-v0.1"
    )
    MARIN_MARIN_8B_INSTRUCT = "marin/marin-8b-instruct"
    MEDIATEK_BREEZE_7B_INSTRUCT = "mediatek/breeze-7b-instruct"
    META_CODELLAMA_70B = "meta/codellama-70b"
    META_LLAMA2_70B = "meta/llama2-70b"
    META_LLAMA3_70B_INSTRUCT = "meta/llama3-70b-instruct"
    META_LLAMA3_8B_INSTRUCT = "meta/llama3-8b-instruct"
    META_LLAMA_3_1_405B_INSTRUCT = "meta/llama-3.1-405b-instruct"
    META_LLAMA_3_1_70B_INSTRUCT = "meta/llama-3.1-70b-instruct"
    META_LLAMA_3_1_8B_INSTRUCT = "meta/llama-3.1-8b-instruct"
    META_LLAMA_3_2_11B_VISION_INSTRUCT = "meta/llama-3.2-11b-vision-instruct"
    META_LLAMA_3_2_1B_INSTRUCT = "meta/llama-3.2-1b-instruct"
    META_LLAMA_3_2_3B_INSTRUCT = "meta/llama-3.2-3b-instruct"
    META_LLAMA_3_2_90B_VISION_INSTRUCT = "meta/llama-3.2-90b-vision-instruct"
    META_LLAMA_3_3_70B_INSTRUCT = "meta/llama-3.3-70b-instruct"
    META_LLAMA_4_MAVERICK_17B_128E_INSTRUCT = "meta/llama-4-maverick-17b-128e-instruct"
    META_LLAMA_4_SCOUT_17B_16E_INSTRUCT = "meta/llama-4-scout-17b-16e-instruct"
    META_LLAMA_GUARD_4_12B = "meta/llama-guard-4-12b"
    MICROSOFT_KOSMOS_2 = "microsoft/kosmos-2"
    MICROSOFT_PHI_3_5_MINI_INSTRUCT = "microsoft/phi-3.5-mini-instruct"
    MICROSOFT_PHI_3_5_MOE_INSTRUCT = "microsoft/phi-3.5-moe-instruct"
    MICROSOFT_PHI_3_5_VISION_INSTRUCT = "microsoft/phi-3.5-vision-instruct"
    MICROSOFT_PHI_3_MEDIUM_128K_INSTRUCT = "microsoft/phi-3-medium-128k-instruct"
    MICROSOFT_PHI_3_MEDIUM_4K_INSTRUCT = "microsoft/phi-3-medium-4k-instruct"
    MICROSOFT_PHI_3_MINI_128K_INSTRUCT = "microsoft/phi-3-mini-128k-instruct"
    MICROSOFT_PHI_3_MINI_4K_INSTRUCT = "microsoft/phi-3-mini-4k-instruct"
    MICROSOFT_PHI_3_SMALL_128K_INSTRUCT = "microsoft/phi-3-small-128k-instruct"
    MICROSOFT_PHI_3_SMALL_8K_INSTRUCT = "microsoft/phi-3-small-8k-instruct"
    MICROSOFT_PHI_3_VISION_128K_INSTRUCT = "microsoft/phi-3-vision-128k-instruct"
    MICROSOFT_PHI_4_MINI_FLASH_REASONING = "microsoft/phi-4-mini-flash-reasoning"
    MICROSOFT_PHI_4_MINI_INSTRUCT = "microsoft/phi-4-mini-instruct"
    MICROSOFT_PHI_4_MULTIMODAL_INSTRUCT = "microsoft/phi-4-multimodal-instruct"
    MINIMAXAI_MINIMAX_M2 = "minimaxai/minimax-m2"
    MINIMAXAI_MINIMAX_M2_1 = "minimaxai/minimax-m2.1"
    MISTRALAI_CODESTRAL_22B_INSTRUCT_V0_1 = "mistralai/codestral-22b-instruct-v0.1"
    MISTRALAI_DEVSTRAL_2_123B_INSTRUCT_2512 = "mistralai/devstral-2-123b-instruct-2512"
    MISTRALAI_MAGISTRAL_SMALL_2506 = "mistralai/magistral-small-2506"
    MISTRALAI_MAMBA_CODESTRAL_7B_V0_1 = "mistralai/mamba-codestral-7b-v0.1"
    MISTRALAI_MATHSTRAL_7B_V0_1 = "mistralai/mathstral-7b-v0.1"
    MISTRALAI_MINISTRAL_14B_INSTRUCT_2512 = "mistralai/ministral-14b-instruct-2512"
    MISTRALAI_MISTRAL_7B_INSTRUCT_V0_2 = "mistralai/mistral-7b-instruct-v0.2"
    MISTRALAI_MISTRAL_7B_INSTRUCT_V0_3 = "mistralai/mistral-7b-instruct-v0.3"
    MISTRALAI_MISTRAL_LARGE = "mistralai/mistral-large"
    MISTRALAI_MISTRAL_LARGE_2_INSTRUCT = "mistralai/mistral-large-2-instruct"
    MISTRALAI_MISTRAL_LARGE_3_675B_INSTRUCT_2512 = "mistralai/mistral-large-3-675b-instruct-2512"
    MISTRALAI_MISTRAL_MEDIUM_3_INSTRUCT = "mistralai/mistral-medium-3-instruct"
    MISTRALAI_MISTRAL_NEMOTRON = "mistralai/mistral-nemotron"
    MISTRALAI_MISTRAL_SMALL_24B_INSTRUCT = "mistralai/mistral-small-24b-instruct"
    MISTRALAI_MISTRAL_SMALL_3_1_24B_INSTRUCT_2503 = "mistralai/mistral-small-3.1-24b-instruct-2503"
    MISTRALAI_MIXTRAL_8X22B_INSTRUCT_V0_1 = "mistralai/mixtral-8x22b-instruct-v0.1"
    MISTRALAI_MIXTRAL_8X22B_V0_1 = "mistralai/mixtral-8x22b-v0.1"
    MISTRALAI_MIXTRAL_8X7B_INSTRUCT_V0_1 = "mistralai/mixtral-8x7b-instruct-v0.1"
    #    MODEL_01_AI_YI_LARGE = "01-ai/yi-large"
    MOONSHOTAI_KIMI_K2_5 = "moonshotai/kimi-k2.5"
    MOONSHOTAI_KIMI_K2_INSTRUCT = "moonshotai/kimi-k2-instruct"
    MOONSHOTAI_KIMI_K2_INSTRUCT_0905 = "moonshotai/kimi-k2-instruct-0905"
    MOONSHOTAI_KIMI_K2_THINKING = "moonshotai/kimi-k2-thinking"
    NVIDIA_COSMOS_REASON2_8B = "nvidia/cosmos-reason2-8b"
    NVIDIA_EMBED_QA_4 = "nvidia/embed-qa-4"
    NVIDIA_LLAMA3_CHATQA_1_5_70B = "nvidia/llama3-chatqa-1.5-70b"
    NVIDIA_LLAMA3_CHATQA_1_5_8B = "nvidia/llama3-chatqa-1.5-8b"
    NVIDIA_LLAMA_3_1_NEMOGUARD_8B_CONTENT_SAFETY = "nvidia/llama-3.1-nemoguard-8b-content-safety"
    NVIDIA_LLAMA_3_1_NEMOGUARD_8B_TOPIC_CONTROL = "nvidia/llama-3.1-nemoguard-8b-topic-control"
    NVIDIA_LLAMA_3_1_NEMOTRON_51B_INSTRUCT = "nvidia/llama-3.1-nemotron-51b-instruct"
    NVIDIA_LLAMA_3_1_NEMOTRON_70B_INSTRUCT = "nvidia/llama-3.1-nemotron-70b-instruct"
    NVIDIA_LLAMA_3_1_NEMOTRON_70B_REWARD = "nvidia/llama-3.1-nemotron-70b-reward"
    NVIDIA_LLAMA_3_1_NEMOTRON_NANO_4B_V1_1 = "nvidia/llama-3.1-nemotron-nano-4b-v1.1"
    NVIDIA_LLAMA_3_1_NEMOTRON_NANO_8B_V1 = "nvidia/llama-3.1-nemotron-nano-8b-v1"
    NVIDIA_LLAMA_3_1_NEMOTRON_NANO_VL_8B_V1 = "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"
    NVIDIA_LLAMA_3_1_NEMOTRON_SAFETY_GUARD_8B_V3 = "nvidia/llama-3.1-nemotron-safety-guard-8b-v3"
    NVIDIA_LLAMA_3_1_NEMOTRON_ULTRA_253B_V1 = "nvidia/llama-3.1-nemotron-ultra-253b-v1"
    NVIDIA_LLAMA_3_2_NEMORETRIEVER_1B_VLM_EMBED_V1 = (
        "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1"
    )
    NVIDIA_LLAMA_3_2_NEMORETRIEVER_300M_EMBED_V1 = "nvidia/llama-3.2-nemoretriever-300m-embed-v1"
    NVIDIA_LLAMA_3_2_NEMORETRIEVER_300M_EMBED_V2 = "nvidia/llama-3.2-nemoretriever-300m-embed-v2"
    NVIDIA_LLAMA_3_2_NV_EMBEDQA_1B_V1 = "nvidia/llama-3.2-nv-embedqa-1b-v1"
    NVIDIA_LLAMA_3_2_NV_EMBEDQA_1B_V2 = "nvidia/llama-3.2-nv-embedqa-1b-v2"
    NVIDIA_LLAMA_3_3_NEMOTRON_SUPER_49B_V1 = "nvidia/llama-3.3-nemotron-super-49b-v1"
    NVIDIA_LLAMA_3_3_NEMOTRON_SUPER_49B_V1_5 = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
    NVIDIA_LLAMA_NEMOTRON_EMBED_VL_1B_V2 = "nvidia/llama-nemotron-embed-vl-1b-v2"
    NVIDIA_MISTRAL_NEMO_MINITRON_8B_8K_INSTRUCT = "nvidia/mistral-nemo-minitron-8b-8k-instruct"
    NVIDIA_MISTRAL_NEMO_MINITRON_8B_BASE = "nvidia/mistral-nemo-minitron-8b-base"
    NVIDIA_NEMORETRIEVER_PARSE = "nvidia/nemoretriever-parse"
    NVIDIA_NEMOTRON_3_NANO_30B_A3B = "nvidia/nemotron-3-nano-30b-a3b"
    NVIDIA_NEMOTRON_4_340B_INSTRUCT = "nvidia/nemotron-4-340b-instruct"
    NVIDIA_NEMOTRON_4_340B_REWARD = "nvidia/nemotron-4-340b-reward"
    NVIDIA_NEMOTRON_4_MINI_HINDI_4B_INSTRUCT = "nvidia/nemotron-4-mini-hindi-4b-instruct"
    NVIDIA_NEMOTRON_CONTENT_SAFETY_REASONING_4B = "nvidia/nemotron-content-safety-reasoning-4b"
    NVIDIA_NEMOTRON_MINI_4B_INSTRUCT = "nvidia/nemotron-mini-4b-instruct"
    NVIDIA_NEMOTRON_NANO_12B_V2_VL = "nvidia/nemotron-nano-12b-v2-vl"
    NVIDIA_NEMOTRON_NANO_3_30B_A3B = "nvidia/nemotron-nano-3-30b-a3b"
    NVIDIA_NEMOTRON_PARSE = "nvidia/nemotron-parse"
    NVIDIA_NEVA_22B = "nvidia/neva-22b"
    NVIDIA_NVCLIP = "nvidia/nvclip"
    NVIDIA_NVIDIA_NEMOTRON_NANO_9B_V2 = "nvidia/nvidia-nemotron-nano-9b-v2"
    NVIDIA_NV_EMBEDCODE_7B_V1 = "nvidia/nv-embedcode-7b-v1"
    NVIDIA_NV_EMBEDQA_E5_V5 = "nvidia/nv-embedqa-e5-v5"
    NVIDIA_NV_EMBEDQA_MISTRAL_7B_V2 = "nvidia/nv-embedqa-mistral-7b-v2"
    NVIDIA_NV_EMBED_V1 = "nvidia/nv-embed-v1"
    NVIDIA_RIVA_TRANSLATE_4B_INSTRUCT = "nvidia/riva-translate-4b-instruct"
    NVIDIA_RIVA_TRANSLATE_4B_INSTRUCT_V1_1 = "nvidia/riva-translate-4b-instruct-v1.1"
    NVIDIA_STREAMPETR = "nvidia/streampetr"
    NVIDIA_USDCODE_LLAMA_3_1_70B_INSTRUCT = "nvidia/usdcode-llama-3.1-70b-instruct"
    NVIDIA_VILA = "nvidia/vila"
    NV_MISTRALAI_MISTRAL_NEMO_12B_INSTRUCT = "nv-mistralai/mistral-nemo-12b-instruct"
    OPENAI_GPT_OSS_120B = "openai/gpt-oss-120b"
    OPENAI_GPT_OSS_20B = "openai/gpt-oss-20b"
    OPENGPT_X_TEUKEN_7B_INSTRUCT_COMMERCIAL_V0_4 = "opengpt-x/teuken-7b-instruct-commercial-v0.4"
    QWEN_QWEN2_5_7B_INSTRUCT = "qwen/qwen2.5-7b-instruct"
    QWEN_QWEN2_5_CODER_32B_INSTRUCT = "qwen/qwen2.5-coder-32b-instruct"
    QWEN_QWEN2_5_CODER_7B_INSTRUCT = "qwen/qwen2.5-coder-7b-instruct"
    QWEN_QWEN2_7B_INSTRUCT = "qwen/qwen2-7b-instruct"
    QWEN_QWEN3_235B_A22B = "qwen/qwen3-235b-a22b"
    QWEN_QWEN3_CODER_480B_A35B_INSTRUCT = "qwen/qwen3-coder-480b-a35b-instruct"
    QWEN_QWEN3_NEXT_80B_A3B_INSTRUCT = "qwen/qwen3-next-80b-a3b-instruct"
    QWEN_QWEN3_NEXT_80B_A3B_THINKING = "qwen/qwen3-next-80b-a3b-thinking"
    QWEN_QWQ_32B = "qwen/qwq-32b"
    RAKUTEN_RAKUTENAI_7B_CHAT = "rakuten/rakutenai-7b-chat"
    RAKUTEN_RAKUTENAI_7B_INSTRUCT = "rakuten/rakutenai-7b-instruct"
    SARVAMAI_SARVAM_M = "sarvamai/sarvam-m"
    SNOWFLAKE_ARCTIC_EMBED_L = "snowflake/arctic-embed-l"
    SPEAKLEASH_BIELIK_11B_V2_3_INSTRUCT = "speakleash/bielik-11b-v2.3-instruct"
    SPEAKLEASH_BIELIK_11B_V2_6_INSTRUCT = "speakleash/bielik-11b-v2.6-instruct"
    STEPFUN_AI_STEP_3_5_FLASH = "stepfun-ai/step-3.5-flash"
    STOCKMARK_STOCKMARK_2_100B_INSTRUCT = "stockmark/stockmark-2-100b-instruct"
    THUDM_CHATGLM3_6B = "thudm/chatglm3-6b"
    TIIUAE_FALCON3_7B_INSTRUCT = "tiiuae/falcon3-7b-instruct"
    TOKYOTECH_LLM_LLAMA_3_SWALLOW_70B_INSTRUCT_V0_1 = (
        "tokyotech-llm/llama-3-swallow-70b-instruct-v0.1"
    )
    UPSTAGE_SOLAR_10_7B_INSTRUCT = "upstage/solar-10.7b-instruct"
    UTTER_PROJECT_EUROLLM_9B_INSTRUCT = "utter-project/eurollm-9b-instruct"
    WRITER_PALMYRA_CREATIVE_122B = "writer/palmyra-creative-122b"
    WRITER_PALMYRA_FIN_70B_32K = "writer/palmyra-fin-70b-32k"
    WRITER_PALMYRA_MED_70B = "writer/palmyra-med-70b"
    WRITER_PALMYRA_MED_70B_32K = "writer/palmyra-med-70b-32k"
    YENTINGLIN_LLAMA_3_TAIWAN_70B_INSTRUCT = "yentinglin/llama-3-taiwan-70b-instruct"
    ZYPHRA_ZAMBA2_7B_INSTRUCT = "zyphra/zamba2-7b-instruct"
    Z_AI_GLM4_7 = "z-ai/glm4.7"


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
    | NvidiaModelName
    | FakeModelName
)


class NvidiaEmbeddingModelName(StrEnum):
    """https://build.nvidia.com/explore/discover"""

    NV_EMBEDQA_MISTRAL_7B_V2 = "nvidia/nv-embedqa-mistral-7b-v2"
    NV_EMBEDQA_E5_V5 = "nvidia/nv-embedqa-e5-v5"


AllEmbeddingModelEnum: TypeAlias = (
    OpenAIEmbeddingModelName
    | GoogleEmbeddingModelName
    | OllamaEmbeddingModelName
    | NvidiaEmbeddingModelName
)
