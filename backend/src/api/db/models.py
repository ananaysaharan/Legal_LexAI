import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

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
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False, unique=True)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    document_type = Column(String, nullable=True)
    version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="pages")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    section = Column(String, nullable=True)
    clause = Column(String, nullable=True)
    text_content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")
