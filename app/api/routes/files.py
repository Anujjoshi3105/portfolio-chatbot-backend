from fastapi import APIRouter, Depends, File, HTTPException, UploadQuery, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, List, Optional

from app.database.models import File, User
from app.database.session import get_async_session
from app.storage.base import get_storage_backend, StorageBackend
from app.core.config import settings
import uuid
import os


router = APIRouter(prefix="/api/v1", tags=["files"])

storage: StorageBackend = get_storage_backend()


async def get_current_user(
    api_key: str = Query(..., description="API key for authentication"),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Dependency to get the current authenticated user."""
    from app.database.models import APIKey

    stmt = (
        session.query(APIKey)
        .filter(APIKey.hash == hash_api_key(api_key))
        .first()
    )
    api_key_obj = stmt[0] if stmt else None

    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")

    user = await session.get(User, api_key_obj.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def hash_api_key(key: str) -> str:
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()


def get_allowed_extensions() -> list[str]:
    return [t.strip().lower() for t in settings.allowed_file_types]


def get_max_upload_size() -> int:
    return settings.MAX_UPLOAD_SIZE


@router.post("/files/upload", response_model=dict)
async def upload_files(
    conversation_id: str | None = Query(None, description="Optional conversation ID to associate files with"),
    files: list[UploadFile] = File(...),
    api_key: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Upload multiple files with validation and persistent storage."""
    from app.database.models import Conversation

    user = await get_current_user(api_key, session)

    # Validate conversation if provided
    conv = None
    if conversation_id:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await session.execute(stmt)
        conv = result.scalar_one_or_none()
        if not conv or conv.user_id != user.id:
            raise HTTPException(status_code=403, detail="Conversation not found or access denied")

    allowed_extensions = get_allowed_extensions()
    max_size = get_max_upload_size()
    uploaded_files = []

    for upload_file in files:
        # Validate file type
        ext = upload_file.filename.rsplit(".", 1)[-1].lower() if "." in upload_file.filename else ""
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type '.{ext}' not allowed. Allowed: {', '.join(allowed_extensions)}",
            )

        # Validate file size
        content = await upload_file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum size of {max_size // (1024 * 1024)}MB",
            )

        # Generate unique storage key
        file_ext = upload_file.filename.rsplit(".", 1)[-1] if "." in upload_file.filename else ""
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        storage_key = unique_filename

        # Upload to storage
        local_temp = f"/tmp/{unique_filename}"
        with open(local_temp, "wb") as f:
            f.write(content)

        result = await storage.upload_file(
            Path(local_temp), storage_key
        )

        # Save metadata to database
        file_record = File(
            id=str(uuid.uuid4()),
            original_name=upload_file.filename,
            storage_key=storage_key,
            mime_type=upload_file.content_type or "application/octet-stream",
            size=len(content),
            user_id=user.id,
            conversation_id=conversation_id if conversation_id else None,
            processing_status="pending",
        )
        session.add(file_record)
        uploaded_files.append({
            "id": file_record.id,
            "original_name": file_record.original_name,
            "storage_key": file_record.storage_key,
            "mime_type": file_record.mime_type,
            "size": file_record.size,
            "processing_status": file_record.processing_status,
        })

        # Clean up temp file
        if os.path.exists(local_temp):
            os.remove(local_temp)

    await session.commit()

    return {
        "files": uploaded_files,
        "count": len(uploaded_files),
        "message": f"Successfully uploaded {len(uploaded_files)} file(s)",
    }


@router.get("/files", response_model=dict)
async def list_files(
    api_key: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 50,
    file_type: str | None = Query(None, description="Filter by file extension"),
    conversation_id: str | None = Query(None, description="Filter by conversation ID"),
) -> Any:
    """List uploaded files with pagination and filters."""
    from app.database.models import File

    user = await get_current_user(api_key, session)

    stmt = select(File).where(File.user_id == user.id)

    if conversation_id:
        stmt = stmt.where(File.conversation_id == conversation_id)

    if file_type:
        ext = file_type.lstrip(".")
        stmt = stmt.where(File.mime_type.contains(ext) | File.original_name.like(f".{ext}"))

    # Count total
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(select(File).where(File.user_id == user.id).subquery())
    if conversation_id:
        count_stmt = count_stmt.where(File.conversation_id == conversation_id)
    if file_type:
        ext = file_type.lstrip(".")
        count_stmt = count_stmt.where(File.mime_type.contains(ext) | File.original_name.like(f".{ext}"))

    count_result = await session.execute(count_stmt)
    total = count_result.scalar_one()

    # Paginate
    stmt = stmt.offset(skip).limit(limit).order_by(File.created_at.desc())
    result = await session.execute(stmt)
    files = result.scalars().all()

    return {
        "files": [
            {
                "id": str(f.id),
                "original_name": f.original_name,
                "storage_key": f.storage_key,
                "mime_type": f.mime_type,
                "size": f.size,
                "is_indexed": f.is_indexed,
                "processing_status": f.processing_status,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "conversation_id": str(f.conversation_id) if f.conversation_id else None,
            }
            for f in files
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/files/{file_id}", response_model=dict)
async def get_file_metadata(
    file_id: str,
    api_key: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Return file metadata."""
    from app.database.models import File

    user = await get_current_user(api_key, session)

    stmt = select(File).where(File.id == file_id, File.user_id == user.id)
    result = await session.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    return {
        "id": str(file_record.id),
        "original_name": file_record.original_name,
        "storage_key": file_record.storage_key,
        "mime_type": file_record.mime_type,
        "size": file_record.size,
        "is_indexed": file_record.is_indexed,
        "processing_status": file_record.processing_status,
        "created_at": file_record.created_at.isoformat() if file_record.created_at else None,
        "conversation_id": str(file_record.conversation_id) if file_record.conversation_id else None,
    }


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    api_key: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Download the original file."""
    from app.database.models import File

    user = await get_current_user(api_key, session)

    stmt = select(File).where(File.id == file_id, File.user_id == user.id)
    result = await session.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    # Download from storage to temp location
    import tempfile
    ext = file_record.storage_key.rsplit(".", 1)[-1] if "." in file_record.storage_key else ""
    local_temp = tempfile.mktemp(suffix=f".{ext}" if ext else "")

    await storage.download_file(file_record.storage_key, Path(local_temp))

    return FileResponse(
        path=local_temp,
        filename=file_record.original_name,
        media_type=file_record.mime_type or "application/octet-stream",
    )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    api_key: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Delete the file and associated indexed content."""
    from app.database.models import File, DocumentChunk, ConversationFile

    user = await get_current_user(api_key, session)

    stmt = select(File).where(File.id == file_id, File.user_id == user.id)
    result = await session.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    # Delete from storage
    await storage.delete_file(file_record.storage_key)

    # Delete document chunks
    from sqlalchemy import delete as sq_delete
    await session.execute(
        sq_delete(DocumentChunk).where(DocumentChunk.file_id == file_id)
    )

    # Delete conversation file links
    await session.execute(
        sq_delete(ConversationFile).where(ConversationFile.file_id == file_id)
    )

    await session.delete(file_record)
    await session.commit()

    return {"message": "File deleted successfully", "file_id": file_id}


@router.get("/files/{file_id}/status", response_model=dict)
async def get_file_status(
    file_id: str,
    api_key: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Return processing and indexing status."""
    from app.database.models import File

    user = await get_current_user(api_key, session)

    stmt = select(File).where(File.id == file_id, File.user_id == user.id)
    result = await session.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    return {
        "file_id": str(file_record.id),
        "processing_status": file_record.processing_status,
        "is_indexed": file_record.is_indexed,
        "error": file_record.error,
    }