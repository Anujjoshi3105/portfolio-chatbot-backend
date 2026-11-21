import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional


class LocalStorage:
    """
    Local filesystem storage backend.
    
    Used as fallback when no HF Storage Bucket is configured.
    Data persists in the configured directory.
    """
    
    def __init__(self, base_path: str = "./data") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, local_path: Path, remote_key: str, overwrite: bool = False) -> Dict[str, Any]:
        """Upload a file to local storage."""
        remote_path = self.base_path / remote_key
        remote_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not overwrite and remote_path.exists():
            raise FileExistsError(f"File already exists: {remote_key}")
        
        content = local_path.read_bytes()
        remote_path.write_bytes(content)
        
        return {
            "storage_key": remote_key,
            "size": remote_path.stat().st_size,
            "url": self._get_file_url(remote_key),
        }
    
    async def download_file(self, remote_key: str, local_path: Path) -> None:
        """Download a file from local storage."""
        remote_path = self.base_path / remote_key
        remote_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not remote_path.exists():
            raise FileNotFoundError(f"File not found: {remote_key}")
        
        content = remote_path.read_bytes()
        local_path.write_bytes(content)
    
    async def delete_file(self, remote_key: str) -> None:
        """Delete a file from local storage."""
        remote_path = self.base_path / remote_key
        if remote_path.exists():
            remote_path.unlink()
    
    async def file_exists(self, remote_key: str) -> bool:
        """Check if a file exists in local storage."""
        remote_path = self.base_path / remote_key
        return remote_path.exists()
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in local storage with optional prefix filter."""
        files = []
        if not self.base_path.exists():
            return files
        
        for p in self.base_path.rglob("*"):
            if p.is_file():
                relative_path = p.relative_to(self.base_path)
                if prefix and not str(relative_path).startswith(prefix.rstrip("/") + "/"):
                    continue
                files.append({
                    "storage_key": str(relative_path),
                    "name": p.name,
                    "size": p.stat().st_size,
                    "path": str(relative_path),
                })
        
        return files
    
    def _get_file_url(self, remote_key: str) -> str:
        """Get a URL to access a file."""
        return f"/api/v1/files/{remote_key}"