import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Storing the Supabase Auth user UUID as a string (or UUID)
    user_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship(
        "Document", back_populates="case", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="case", cascade="all, delete-orphan"
    )
    executions = relationship(
        "AIExecution", back_populates="case", cascade="all, delete-orphan"
    )
    memories = relationship(
        "CaseMemory", back_populates="case", cascade="all, delete-orphan"
    )
    generated_documents = relationship(
        "GeneratedDocument", back_populates="case", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False, unique=True)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    document_type = Column(String, nullable=True)
    version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="documents")
    pages = relationship(
        "DocumentPage", back_populates="document", cascade="all, delete-orphan"
    )
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="pages")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    section = Column(String, nullable=True)
    clause = Column(String, nullable=True)
    text_content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    case = relationship("Case", back_populates="conversations")
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class AIExecution(Base):
    """Durable record of one AI-engine request for audit, memory, and evaluation."""

    __tablename__ = "ai_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(String, nullable=False, index=True)
    request_text = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    intent_data = Column(JSONB, nullable=True)
    plan_data = Column(JSONB, nullable=True)
    trace_data = Column(JSONB, nullable=False, default=list)
    result_data = Column(JSONB, nullable=True)
    error_data = Column(JSONB, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    case = relationship("Case", back_populates="executions")


class CaseMemory(Base):
    """Curated, case-scoped memory. This is not a raw chat transcript."""

    __tablename__ = "case_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_type = Column(String(80), nullable=False, index=True)
    memory_key = Column(String(255), nullable=True, index=True)
    content = Column(Text, nullable=False)
    metadata_data = Column(JSONB, nullable=False, default=dict)
    source_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    case = relationship("Case", back_populates="memories")


class UserPreferenceMemory(Base):
    """Long-lived, cross-case user preferences. Never store case facts here."""

    __tablename__ = "user_preference_memories"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "preference_key", "scope", name="uq_user_preference_scope"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    preference_type = Column(String(80), nullable=False, index=True)
    preference_key = Column(String(120), nullable=False)
    preference_value = Column(JSONB, nullable=False)
    scope = Column(String(80), nullable=False, default="global")
    metadata_data = Column(JSONB, nullable=False, default=dict)
    confidence = Column(Integer, nullable=False, default=100)
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class GeneratedDocument(Base):
    """A versioned AI-produced legal artifact, distinct from chat and uploaded sources."""

    __tablename__ = "generated_documents"
    __table_args__ = (
        UniqueConstraint(
            "case_id", "document_key", "version", name="uq_generated_document_version"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("generated_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    document_type = Column(String(80), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    document_key = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="draft")
    edit_operation = Column(String(30), nullable=False, default="generate")
    edit_instructions = Column(Text, nullable=True)
    metadata_data = Column(JSONB, nullable=False, default=dict)
    citations_data = Column(JSONB, nullable=False, default=list)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    case = relationship("Case", back_populates="generated_documents")
    parent_document = relationship("GeneratedDocument", remote_side=[id])


class BackgroundJob(Base):
    """Durable status record for work delegated to background workers."""

    __tablename__ = "background_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    case_id = Column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True
    )
    job_type = Column(String(80), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="queued", index=True)
    payload_data = Column(JSONB, nullable=False, default=dict)
    result_data = Column(JSONB, nullable=True)
    error_data = Column(JSONB, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    celery_task_id = Column(String(255), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
