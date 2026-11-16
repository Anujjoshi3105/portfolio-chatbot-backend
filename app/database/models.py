import uuid

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def _uuid4() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid4)
    api_key_hash = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    conversations = relationship("Conversation", back_populates="owner", cascade="all, delete-orphan")
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_users_api_key_hash", "api_key_hash", unique=True),)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=_uuid4)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")
    conversations = relationship("Conversation", back_populates="created_by_key", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_api_keys_user_id", "user_id"),
        Index("ix_api_keys_hash", "hash", unique=True),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=_uuid4)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    is_private = Column(Boolean, default=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_by_key_id = Column(String, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    owner = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    files = relationship("ConversationFile", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_conversations_user_id", "user_id"),
        Index("ix_conversations_is_private", "is_private"),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=_uuid4)
    conversation_id = Column(
        String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_conversation_id", "conversation_id"),
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )


class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=_uuid4)
    original_name = Column(String, nullable=False)
    storage_key = Column(String, nullable=False, unique=True)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(
        String, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    is_indexed = Column(Boolean, default=False)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    owner = relationship("User", back_populates="files")
    conversation_links = relationship(
        "ConversationFile", back_populates="file", cascade="all, delete-orphan"
    )
    chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_files_user_id", "user_id"),
        Index("ix_files_conversation_id", "conversation_id"),
        Index("ix_files_storage_key", "storage_key", unique=True),
        Index("ix_files_processing_status", "processing_status"),
    )


class ConversationFile(Base):
    __tablename__ = "conversation_files"

    id = Column(String, primary_key=True, default=_uuid4)
    conversation_id = Column(
        String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    file_id = Column(String, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="files")
    file = relationship("File", back_populates="conversation_links")

    __table_args__ = (
        UniqueConstraint("conversation_id", "file_id", name="uq_conversation_file"),
        Index("ix_conversation_file_conversation", "conversation_id"),
        Index("ix_conversation_file_file", "file_id"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=_uuid4)
    file_id = Column(String, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)
    chunk_metadata = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    file = relationship("File", back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunks_file_id", "file_id"),
        Index("ix_document_chunks_chunk_index", "chunk_index"),
    )


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String, primary_key=True, default=_uuid4)
    file_id = Column(String, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    kind = Column(String, nullable=False)  # "ingest", "embed", "reindex"
    progress = Column(Float, default=0.0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    file = relationship("File", back_populates="processing_jobs")
    user = relationship("User", back_populates="processing_jobs")

    __table_args__ = (
        Index("ix_processing_jobs_file_id", "file_id"),
        Index("ix_processing_jobs_status", "status"),
    )


class ModelConfiguration(Base):
    __tablename__ = "model_configurations"

    id = Column(String, primary_key=True, default=_uuid4)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    base_url = Column(String, nullable=True)
    api_key_name = Column(String, nullable=True)  # env var name
    parameters = Column(JSON, default=dict, nullable=True)  # temperature, max_tokens, etc.
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_model_configurations_provider", "provider"),
        Index("ix_model_configurations_name", "name"),
        Index("ix_model_configurations_default", "is_default"),
    )