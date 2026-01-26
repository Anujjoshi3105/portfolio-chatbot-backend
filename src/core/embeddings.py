from functools import cache
from typing import TypeAlias

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from core.settings import settings
from schema.models import (
    AllEmbeddingModelEnum,
    GoogleEmbeddingModelName,
    OllamaEmbeddingModelName,
    OpenAIEmbeddingModelName,
)

EmbeddingT: TypeAlias = (
    OpenAIEmbeddings
    | GoogleGenerativeAIEmbeddings
    | OllamaEmbeddings
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
    
    raise ValueError(f"Unsupported embedding model: {model_name}")
