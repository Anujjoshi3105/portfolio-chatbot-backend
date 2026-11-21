import os
from pathlib import Path
import tempfile
from typing import Any, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select, delete as sq_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import File as DBFile, User, Conversation, DocumentChunk, ConversationFile
from app.database.session import get_async_session
from app.core.security import get_current_user
from app.storage import get_storage_backend, StorageBackend
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["files"])

storage: StorageBackend = get_storage_backend()


def get_allowed_extensions() -> list[str]:
    return [t.strip().lower() for t in settings.allowed_file_types]


def get_max_upload_size() -> int:
    return settings.MAX_UPLOAD_SIZE


@router.post("/files/upload", response_model=dict)
async def upload_files(
    conversation_id: str | None = Query(None, description="Optional conversation ID to associate files with"),
    files: list[UploadFile] = FastAPIFile(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Upload multiple files with validation and persistent storage."""
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
        filename = upload_file.filename or "file"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type '.{ext}' not allowed. Allowed: {', '.join(allowed_extensions)}",
            )

        content = await upload_file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum size of {max_size // (1024 * 1024)}MB",
            )

        file_ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        unique_filename = f"{uuid.uuid4()}.{file_ext}" if file_ext else str(uuid.uuid4())
        storage_key = unique_filename

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}" if file_ext else "") as tmp:
            tmp.write(content)
            local_temp = tmp.name

        try:
            await storage.upload_file(Path(local_temp), storage_key)
        finally:
            if os.path.exists(local_temp):
                os.remove(local_temp)

        file_record = DBFile(
            id=str(uuid.uuid4()),
            original_name=filename,
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

    await session.commit()

    return {
        "files": uploaded_files,
        "count": len(uploaded_files),
        "message": f"Successfully uploaded {len(uploaded_files)} file(s)",
    }


@router.get("/files", response_model=dict)
async def list_files(
    skip: int = 0,
    limit: int = 50,
    file_type: str | None = Query(None, description="Filter by file extension"),
    conversation_id: str | None = Query(None, description="Filter by conversation ID"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """List uploaded files with pagination and filters."""
    stmt = select(DBFile).where(DBFile.user_id == user.id)

    if conversation_id:
        stmt = stmt.where(DBFile.conversation_id == conversation_id)

    if file_type:
        ext = file_type.lstrip(".")
        stmt = stmt.where(DBFile.mime_type.contains(ext) | DBFile.original_name.like(f"%.{ext}"))

    count_stmt = select(func.count(DBFile.id)).where(DBFile.user_id == user.id)
    if conversation_id:
        count_stmt = count_stmt.where(DBFile.conversation_id == conversation_id)
    if file_type:
        ext = file_type.lstrip(".")
        count_stmt = count_stmt.where(DBFile.mime_type.contains(ext) | DBFile.original_name.like(f"%.{ext}"))

    count_result = await session.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = stmt.offset(skip).limit(limit).order_by(DBFile.created_at.desc())
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
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Return file metadata."""
    stmt = select(DBFile).where(DBFile.id == file_id, DBFile.user_id == user.id)
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
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Download the original file."""
    stmt = select(DBFile).where(DBFile.id == file_id, DBFile.user_id == user.id)
    result = await session.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    ext = file_record.storage_key.rsplit(".", 1)[-1] if "." in file_record.storage_key else ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}" if ext else "") as tmp:
        local_temp = tmp.name

    await storage.download_file(file_record.storage_key, Path(local_temp))

    return FileResponse(
        path=local_temp,
        filename=file_record.original_name,
        media_type=file_record.mime_type or "application/octet-stream",
    )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Delete the file and associated indexed content."""
    stmt = select(DBFile).where(DBFile.id == file_id, DBFile.user_id == user.id)
    result = await session.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    await storage.delete_file(file_record.storage_key)

    await session.execute(
        sq_delete(DocumentChunk).where(DocumentChunk.file_id == file_id)
    )
    await session.execute(
        sq_delete(ConversationFile).where(ConversationFile.file_id == file_id)
    )

    await session.delete(file_record)
    await session.commit()

    return {"message": "File deleted successfully", "file_id": file_id}


@router.get("/files/{file_id}/status", response_model=dict)
async def get_file_status(
    file_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Return processing and indexing status."""
    stmt = select(DBFile).where(DBFile.id == file_id, DBFile.user_id == user.id)
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
