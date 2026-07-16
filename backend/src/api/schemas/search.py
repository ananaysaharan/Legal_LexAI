from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResultChunk(BaseModel):
    document_id: UUID
    page_number: int
    section: Optional[str] = None
    clause: Optional[str] = None
    text_content: str
    similarity_score: float

class SearchResponse(BaseModel):
    results: List[SearchResultChunk]
