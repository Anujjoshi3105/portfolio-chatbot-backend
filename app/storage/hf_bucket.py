import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

try:
    from huggingface_hub import HfApi, HfDatasetQualityWarning
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


class HFBucketStorage:
    """
    Storage backend using Hugging Face Storage Buckets.
    
    HF_STORAGE_BUCKET_NAME must be set in environment variables.
    Buckets are mounted at /data/<bucket_name>/ in the container.
    """
    
    def __init__(self) -> None:
        self.bucket_name = os.getenv("HF_STORAGE_BUCKET_NAME")
        self.mount_path = os.getenv("HF_STORAGE_MOUNT_PATH", "/data")
        self._local_base = Path(self.mount_path) / self.bucket_name if self.bucket_name else Path("local_storage")
        
        if self.bucket_name:
            self._local_path = self._local_base
            self._local_path.mkdir(parents=True, exist_ok=True)
        else:
            self._local_path = Path("./local_storage_fallback")
            self._local_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, local_path: Path, remote_key: str, overwrite: bool = False) -> Dict[str, Any]:
        """Upload a file to the HF Storage Bucket."""
        remote_path = self._local_path / remote_key
        remote_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not overwrite and remote_path.exists():
            raise HTTPException(status_code=409, detail=f"File already exists: {remote_key}")
        
        import shutil
        shutil.copy2(str(local_path), str(remote_path))
        
        return {
            "storage_key": remote_key,
            "size": remote_path.stat().st_size,
            "url": self._get_file_url(remote_key),
        }
    
    async def download_file(self, remote_key: str, local_path: Path) -> None:
        """Download a file from the HF Storage Bucket."""
        remote_path = self._local_path / remote_key
        remote_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not remote_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {remote_key}")
        
        import shutil
        shutil.copy2(str(remote_path), str(local_path))
    
    async def delete_file(self, remote_key: str) -> None:
        """Delete a file from the HF Storage Bucket."""
        remote_path = self._local_path / remote_key
        remote_path.parent.mkdir(parents=True, exist_ok=True)
        
        if remote_path.exists():
            remote_path.unlink()
    
    async def file_exists(self, remote_key: str) -> bool:
        """Check if a file exists in the HF Storage Bucket."""
        remote_path = self._local_path / remote_key
        return remote_path.exists()
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in the HF Storage Bucket with optional prefix filter."""
        files = []
        if not self._local_path.exists():
            return files
        
        for p in self._local_path.rglob("*"):
            if p.is_file():
                relative_path = p.relative_to(self._local_path)
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
        """Get a URL to access a file in the HF Storage Bucket."""
        if self.bucket_name:
            return f"https://huggingface.co/datasets/{self.bucket_name}/resolve/main/{remote_key}"
        return f"/api/v1/files/{remote_key}"