from enum import Enum
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator


class IntentType(str, Enum):
    QUESTION_ANSWERING = "question_answering"
    CONTRACT_REVIEW = "contract_review"
    DOCUMENT_SUMMARY = "document_summary"
    AGREEMENT_COMPARISON = "agreement_comparison"
    RESPONSE_DRAFTING = "response_drafting"
    RISK_CLAUSE_ANALYSIS = "risk_clause_analysis"
    UNKNOWN = "unknown"


class IntentDetectionRequest(BaseModel):
    request: str = Field(..., min_length=1, max_length=4_000)

    @field_validator("request")
    @classmethod
    def request_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("request must not be blank")
        return value


class Intent(BaseModel):
    """Planner-independent classification of what the user is asking to do."""

    task_type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    normalized_request: str
    matched_signals: List[str]
    requires_retrieval: bool = True
    requires_multiple_documents: bool = False
    detector: Literal["rule_based"] = "rule_based"
