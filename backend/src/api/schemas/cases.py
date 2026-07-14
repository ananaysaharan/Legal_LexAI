from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class CaseBase(BaseModel):
    title: str
    description: Optional[str] = None

class CaseCreate(CaseBase):
    pass

class CaseResponse(CaseBase):
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentBase(BaseModel):
    filename: str
    content_type: str
    size_bytes: int

class DocumentResponse(DocumentBase):
    id: UUID
    case_id: UUID
    storage_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CaseWithDocumentsResponse(CaseResponse):
    documents: List[DocumentResponse] = []
