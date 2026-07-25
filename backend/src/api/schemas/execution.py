from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.api.schemas.orchestration import OrchestrationResponse


class AIExecutionRequest(BaseModel):
    case_id: UUID
    request: str = Field(..., min_length=1, max_length=4_000)
    top_k: int = Field(default=5, ge=1, le=50)

    @field_validator("request")
    @classmethod
    def request_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("request must not be blank")
        return value


class AIExecutionResponse(BaseModel):
    execution_id: UUID
    status: Literal["completed", "failed"]
    workflow: OrchestrationResponse
