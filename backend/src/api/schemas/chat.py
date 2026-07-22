from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.api.schemas.search import SearchResultChunk


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4_000)
    conversation_id: Optional[UUID] = None
    top_k: int = Field(default=5, ge=1, le=50)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class Citation(BaseModel):
    """A frontend-ready pointer to evidence included in the LLM prompt."""

    source_label: str
    document_name: str
    page_number: int
    chunk_id: UUID


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    sources: List[SearchResultChunk]
    citations: List[Citation] = Field(..., min_length=1)
    prompt_template_version: str
