"""Storage backends for the HF Spaces chatbot backend."""

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Storage backend implementations
from app.storage.base import StorageBackend  # noqa: F401
from app.storage.hf_bucket import HFBucketStorage  # noqa: F401
from app.storage.local import LocalStorage  # noqa: F401


def get_storage_backend() -> StorageBackend:
    """Factory function to get the appropriate storage backend based on configuration."""
    from app.core.config import settings

    bucket_name = getattr(settings, "HF_STORAGE_BUCKET_NAME", None)
    if bucket_name:
        return HFBucketStorage()
    return LocalStorage(base_path=getattr(settings, "STORAGE_BASE_PATH", "./data"))