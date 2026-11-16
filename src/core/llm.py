from functools import cache
from typing import TypeAlias

from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrock
from langchain_community.chat_models import FakeListChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from core.settings import Provider, settings
from schema.models import (
    AnthropicModelName,
    AWSModelName,
    AzureOpenAIModelName,
    DeepseekModelName,
    FakeModelName,
    GoogleModelName,
    GroqModelName,
    NvidiaModelName,
    OllamaModelName,
    OpenAICompatibleName,
    OpenAIModelName,
    OpenRouterModelName,
    VertexAIModelName,
)

_MODELS_BY_PROVIDER: dict[Provider, tuple] = {
    Provider.OPENAI: OpenAIModelName,
    Provider.OPENAI_COMPATIBLE: OpenAICompatibleName,
    Provider.AZURE_OPENAI: AzureOpenAIModelName,
    Provider.DEEPSEEK: DeepseekModelName,
    Provider.ANTHROPIC: AnthropicModelName,
    Provider.GOOGLE: GoogleModelName,
    Provider.VERTEXAI: VertexAIModelName,
    Provider.NVIDIA: NvidiaModelName,
    Provider.GROQ: GroqModelName,
    Provider.AWS: AWSModelName,
    Provider.OLLAMA: OllamaModelName,
    Provider.OPENROUTER: OpenRouterModelName,
    Provider.FAKE: FakeModelName,
}


class FakeToolModel(FakeListChatModel):
    def __init__(self, responses: list[str]):
        super().__init__(responses=responses)

    def bind_tools(self, tools):
        return self


ModelT: TypeAlias = (
    AzureChatOpenAI
    | ChatOpenAI
    | ChatAnthropic
    | ChatGoogleGenerativeAI
    | ChatVertexAI
    | ChatGroq
    | ChatBedrock
    | ChatOllama
    | ChatNVIDIA
    | FakeToolModel
)


@cache
def get_model(model_name: str, /) -> ModelT:
    # NOTE: models with streaming=True will send tokens as they are generated
    # if the /stream endpoint is called with stream_tokens=True (the default)
    provider = settings.MODEL_PROVIDER_MAP.get(model_name)
    if provider is None:
        raise ValueError(f"Unsupported model: {model_name}")
    return _build_model(provider, model_name)


def _build_model(provider: Provider, model_name: str) -> ModelT:
    if provider == Provider.OPENAI:
        return ChatOpenAI(model=model_name, streaming=True)
    if provider == Provider.OPENAI_COMPATIBLE:
        if not settings.COMPATIBLE_BASE_URL or not settings.COMPATIBLE_MODEL:
            raise ValueError("OpenAICompatible base url and endpoint must be configured")
        return ChatOpenAI(
            model=settings.COMPATIBLE_MODEL,
            temperature=0.5,
            streaming=True,
            openai_api_base=settings.COMPATIBLE_BASE_URL,
            openai_api_key=settings.COMPATIBLE_API_KEY,
        )
    if provider == Provider.AZURE_OPENAI:
        if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT:
            raise ValueError("Azure OpenAI API key and endpoint must be configured")
        return AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            deployment_name=model_name,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            temperature=0.5,
            streaming=True,
            timeout=60,
            max_retries=3,
        )
    if provider == Provider.DEEPSEEK:
        return ChatOpenAI(
            model=model_name,
            temperature=0.5,
            streaming=True,
            openai_api_base="https://api.deepseek.com",
            openai_api_key=settings.DEEPSEEK_API_KEY,
        )
    if provider == Provider.ANTHROPIC:
        return ChatAnthropic(model=model_name, temperature=0.5, streaming=True)
    if provider == Provider.GOOGLE:
        return ChatGoogleGenerativeAI(model=model_name, temperature=0.5, streaming=True)
    if provider == Provider.VERTEXAI:
        return ChatVertexAI(model=model_name, temperature=0.5, streaming=True)
    if provider == Provider.NVIDIA:
        return ChatNVIDIA(
            model=model_name,
            temperature=0.5,
            api_key=settings.NVIDIA_API_KEY,
        )
    if provider == Provider.GROQ:
        return ChatGroq(model=model_name, temperature=0.5)  # type: ignore[call-arg]
    if provider == Provider.AWS:
        return ChatBedrock(model_id=model_name, temperature=0.5)
    if provider == Provider.OLLAMA:
        if settings.OLLAMA_BASE_URL:
            return ChatOllama(model=model_name, temperature=0.5, base_url=settings.OLLAMA_BASE_URL)
        return ChatOllama(model=model_name, temperature=0.5)
    if provider == Provider.OPENROUTER:
        return ChatOpenAI(
            model=model_name,
            temperature=0.5,
            streaming=True,
            base_url="https://openrouter.ai/api/v1/",
            api_key=settings.OPENROUTER_API_KEY,
        )
    if provider == Provider.FAKE:
        return FakeToolModel(responses=["This is a test response from the fake model."])

    raise ValueError(f"Unsupported model: {model_name}")
