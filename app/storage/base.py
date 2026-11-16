from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiofiles


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def upload_file(self, local_path: Path, remote_key: str, overwrite: bool = False) -> Dict[str, Any]:
        """Upload a file to storage."""
        pass

    @abstractmethod
    async def download_file(self, remote_key: str, local_path: Path) -> None:
        """Download a file from storage."""
        pass

    @abstractmethod
    async def delete_file(self, remote_key: str) -> None:
        """Delete a file from storage."""
        pass

    @abstractmethod
    async def file_exists(self, remote_key: str) -> bool:
        """Check if a file exists in storage."""
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in storage with optional prefix filter."""
        pass

    @abstractmethod
    async def get_file_url(self, remote_key: str, expires_in: int = 3600) -> str:
        """Get a URL to access a file."""
        pass