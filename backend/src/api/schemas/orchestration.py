from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.api.schemas.intent import Intent
from src.api.schemas.planner import ExecutionPlan
from src.api.schemas.workers import (
    AnalysisWorkerOutput,
    ResearchWorkerOutput,
    ReviewerWorkerOutput,
    WriterWorkerOutput,
)


class OrchestrationRequest(BaseModel):
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


class FinalResponse(BaseModel):
    content: str
    source_ids: List[str]
    review_passed: bool
    requires_human_review: bool = True


class OrchestrationFailure(BaseModel):
    node: str
    message: str


class OrchestrationResponse(BaseModel):
    status: Literal["completed", "failed"]
    trace: List[str]
    intent: Optional[Intent] = None
    plan: Optional[ExecutionPlan] = None
    research: Optional[ResearchWorkerOutput] = None
    analysis: Optional[AnalysisWorkerOutput] = None
    writer: Optional[WriterWorkerOutput] = None
    reviewer: Optional[ReviewerWorkerOutput] = None
    final_response: Optional[FinalResponse] = None
    error: Optional[OrchestrationFailure] = None
