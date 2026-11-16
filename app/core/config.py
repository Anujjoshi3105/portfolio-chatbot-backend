import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import os
from dotenv import find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core configuration for the HF Spaces chatbot backend."""
    
    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 7860
    DEBUG: bool = False
    
    # Storage configuration
    HF_STORAGE_BUCKET_NAME: str | None = Field(None, env="HF_STORAGE_BUCKET_NAME")
    STORAGE_BASE_PATH: str = Field("./data", env="STORAGE_BASE_PATH")
    
    # LLM configuration
    LLM_PROVIDER: str = Field("nvidia", env="LLM_PROVIDER")
    NVIDIA_API_KEY: str | None = Field(None, env="NVIDIA_API_KEY")
    NVIDIA_BASE_URL: str | None = Field(None, env="NVIDIA_BASE_URL")
    NVIDIA_MODEL: str | None = Field(None, env="NVIDIA_MODEL")
    COMPATIBLE_API_KEY: str | None = Field(None, env="COMPATIBLE_API_KEY")
    COMPATIBLE_BASE_URL: str | None = Field(None, env="COMPATIBLE_BASE_URL")
    COMPATIBLE_MODEL: str | None = Field(None, env="COMPATIBLE_MODEL")
    
    # Security
    API_KEY_NAME: str = Field("x-api-key", env="API_KEY_NAME")
    RATE_LIMIT_PER_MINUTE: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    
    # Database
    DATABASE_TYPE: str = Field("sqlite", env="DATABASE_TYPE")
    SQLITE_DB_PATH: str = Field("sqlite.db", env="SQLITE_DB_PATH")
    POSTGRES_URL: str | None = Field(None, env="POSTGRES_URL")
    
    # Upload limits
    MAX_UPLOAD_SIZE: int = Field(10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: str = Field(
        "pdf,docx,txt,mdx,csv,json,jpg,jpeg,png,webp,zip",
        env="ALLOWED_FILE_TYPES",
    )
    
    # HF specific
    HF_SPACE_NAME: str | None = Field(None, env="HF_SPACE_NAME")
    
    @property
    def allowed_file_types(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_FILE_TYPES.split(",")]
    
    @property
    def storage_backend(self) -> str:
        if self.HF_STORAGE_BUCKET_NAME:
            return "hf_bucket"
        return "local"
    
    @property
    def is_dev(self) -> bool:
        return self.MODE == "dev" if hasattr(self, "MODE") else False


def find_dotenv() -> str:
    """Find .env file, preferring the one in the project root."""
    for path in [".env", "../.env", "../../.env"]:
        p = Path(path)
        if p.exists():
            return str(p)
    return ""


settings = Settings()