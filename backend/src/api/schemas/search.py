from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

class SearchRequest(BaseModel):
    """Input to retrieval; deliberately contains no generation settings."""

    query: str = Field(..., min_length=1, max_length=4_000)
    top_k: int = Field(default=5, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value

class SearchResultChunk(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_filename: str
    document_type: Optional[str] = None
    document_version: Optional[str] = None
    page_number: int
    chunk_index: int
    section: Optional[str] = None
    clause: Optional[str] = None
    text_content: str
    similarity_score: float

class SearchResponse(BaseModel):
    results: List[SearchResultChunk]
