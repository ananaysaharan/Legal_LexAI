from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GeneratedDocumentType(str, Enum):
    LEGAL_SUMMARY = "legal_summary"
    CASE_REPORT = "case_report"
    DRAFT_CONTRACT = "draft_contract"
    RESPONSE_LETTER = "response_letter"
    INTERNAL_LEGAL_NOTE = "internal_legal_note"


class DocumentEditOperation(str, Enum):
    GENERATE = "generate"
    REWRITE = "rewrite"
    IMPROVE = "improve"
    SIMPLIFY = "simplify"
    EXPAND = "expand"
    SHORTEN = "shorten"
    EXPLAIN = "explain"
    MANUAL_EDIT = "manual_edit"
    RESTORE = "restore"


class GeneratedDocumentCreate(BaseModel):
    case_id: UUID
    document_type: GeneratedDocumentType
    title: str = Field(..., min_length=1, max_length=255)
    instructions: str = Field(..., min_length=1, max_length=4_000)
    document_key: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=5, ge=1, le=50)

    @field_validator("title", "instructions")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


class GeneratedDocumentResponse(BaseModel):
    id: UUID
    case_id: UUID
    source_execution_id: UUID | None
    parent_document_id: UUID | None
    document_type: GeneratedDocumentType
    title: str
    document_key: str
    content: str
    version: int
    status: str
    edit_operation: DocumentEditOperation
    edit_instructions: str | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_data")
    citations: list[str] = Field(validation_alias="citations_data")

    model_config = ConfigDict(from_attributes=True)


class DocumentEditRequest(BaseModel):
    operation: DocumentEditOperation
    instructions: str = Field(..., min_length=1, max_length=4_000)
    top_k: int = Field(default=5, ge=1, le=50)

    @field_validator("instructions")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("instructions must not be blank")
        return value


class DocumentSaveRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=100_000)
    instructions: str | None = Field(default=None, max_length=4_000)


class DocumentExportMetadata(BaseModel):
    document_id: UUID
    title: str
    document_type: GeneratedDocumentType
    version: int
    status: str
    source_execution_id: UUID | None
    parent_document_id: UUID | None
    edit_operation: DocumentEditOperation
    edit_instructions: str | None
    citations: list[str]
    metadata: dict[str, Any]
