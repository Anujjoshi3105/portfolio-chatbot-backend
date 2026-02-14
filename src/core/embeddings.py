from functools import cache
from typing import TypeAlias

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from core.settings import settings
from schema.models import (
    AllEmbeddingModelEnum,
    GoogleEmbeddingModelName,
    OllamaEmbeddingModelName,
    OpenAIEmbeddingModelName,
    NvidiaEmbeddingModelName,
)

EmbeddingT: TypeAlias = (
    OpenAIEmbeddings
    | GoogleGenerativeAIEmbeddings
    | OllamaEmbeddings
    | NVIDIAEmbeddings
)


@cache
def get_embeddings(model_name: AllEmbeddingModelEnum, /) -> EmbeddingT:
    if model_name in OpenAIEmbeddingModelName:
        return OpenAIEmbeddings(model=model_name.value)
    
    if model_name in GoogleEmbeddingModelName:
        return GoogleGenerativeAIEmbeddings(model=model_name.value)
    
    if model_name in OllamaEmbeddingModelName:
        return OllamaEmbeddings(
            model=settings.OLLAMA_EMBEDDING_MODEL or model_name.value,
            base_url=settings.OLLAMA_BASE_URL,
        )
    
    if model_name in NvidiaEmbeddingModelName:
        return NVIDIAEmbeddings(
            model=model_name.value,
            api_key=settings.NVIDIA_API_KEY.get_secret_value() if settings.NVIDIA_API_KEY else None,
        )
    
    raise ValueError(f"Unsupported embedding model: {model_name}")
