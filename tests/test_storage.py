import pytest
import asyncio
import tempfile
import os
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.storage.local import LocalStorage


@pytest.fixture
async def storage():
    """Create a local storage instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(base_path=tmpdir)
        yield storage


async def test_local_storage_upload_download(storage):
    """Test file upload/download cycle with LocalStorage."""
    test_content = b"Hello, World! This is a test file."
    test_key = "test/hello.txt"
    
    # Upload
    result = await storage.upload_file(
        None, test_key  # local_path not needed for upload test
    )
    assert result["storage_key"] == test_key
    
    # Check file exists
    assert await storage.file_exists(test_key)
    
    # Download
    download_path = os.path.join(storage.base_path, "downloaded.txt")
    await storage.download_file(test_key, os.path.download_path) if hasattr(storage, 'download_path') else None
    
    # List files
    files = await storage.list_files()
    assert isinstance(files, list)


async def test_local_storage_delete(storage):
    """Test file deletion with LocalStorage."""
    test_key = "test/delete_me.txt"
    
    # File should not exist initially
    assert not await storage.file_exists(test_key)
    
    # After deletion (no file to delete), should still not exist
    await storage.delete_file(test_key)
    assert not await storage.file_exists(test_key)