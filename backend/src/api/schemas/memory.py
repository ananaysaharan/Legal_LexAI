from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CaseMemoryType(str, Enum):
    CONVERSATION_SUMMARY = "conversation_summary"
    LEGAL_ENTITY = "legal_entity"
    GENERATED_REPORT = "generated_report"
    IMPORTANT_FINDING = "important_finding"
    PLANNER_EXECUTION_SUMMARY = "planner_execution_summary"


class CaseMemoryCreate(BaseModel):
    memory_type: CaseMemoryType
    memory_key: Optional[str] = Field(default=None, max_length=255)
    content: str = Field(..., min_length=1, max_length=20_000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_execution_id: Optional[UUID] = None
    source_document_id: Optional[UUID] = None
    source_conversation_id: Optional[UUID] = None

    @field_validator("content")
    @classmethod
    def trim_required_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


class CaseMemoryResponse(BaseModel):
    id: UUID
    case_id: UUID
    memory_type: CaseMemoryType
    memory_key: Optional[str]
    content: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_data")
    source_execution_id: Optional[UUID]
    source_document_id: Optional[UUID]
    source_conversation_id: Optional[UUID]

    model_config = ConfigDict(from_attributes=True)


class CaseMemoryUpdate(BaseModel):
    memory_key: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = Field(default=None, min_length=1, max_length=20_000)
    metadata: Optional[dict[str, Any]] = None
    source_execution_id: Optional[UUID] = None
    source_document_id: Optional[UUID] = None
    source_conversation_id: Optional[UUID] = None

    @field_validator("content")
    @classmethod
    def trim_optional_content(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value


class UserPreferenceType(str, Enum):
    PREFERRED_REPORT_FORMAT = "preferred_report_format"
    WRITING_STYLE = "writing_style"
    CITATION_PREFERENCES = "citation_preferences"
    WORKFLOW_BEHAVIOR = "workflow_behavior"
    FREQUENTLY_USED_TASK = "frequently_used_task"
    CUSTOM = "custom"


class PreferenceUpdateStrategy(str, Enum):
    REPLACE = "replace"
    MERGE = "merge"
    INCREMENT_USAGE = "increment_usage"


class UserPreferenceMemoryUpsert(BaseModel):
    preference_type: UserPreferenceType
    preference_key: str = Field(..., min_length=1, max_length=120)
    preference_value: dict[str, Any]
    scope: str = Field(default="global", min_length=1, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: int = Field(default=100, ge=0, le=100)
    update_strategy: PreferenceUpdateStrategy = PreferenceUpdateStrategy.REPLACE

    @field_validator("preference_key", "scope")
    @classmethod
    def trim_required_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @model_validator(mode="after")
    def reject_conversation_payloads(self) -> "UserPreferenceMemoryUpsert":
        forbidden_keys = {
            "conversation",
            "conversations",
            "transcript",
            "chat_history",
            "message_content",
            "messages",
        }

        def validate_keys(value: Any) -> None:
            if isinstance(value, dict):
                for key, nested_value in value.items():
                    if str(key).strip().lower() in forbidden_keys:
                        raise ValueError(
                            "user preference memory must not store conversations or transcripts"
                        )
                    validate_keys(nested_value)
            elif isinstance(value, list):
                for nested_value in value:
                    validate_keys(nested_value)

        validate_keys(self.preference_value)
        validate_keys(self.metadata)
        return self


class UserPreferenceMemoryResponse(BaseModel):
    id: UUID
    user_id: str
    preference_type: UserPreferenceType
    preference_key: str
    preference_value: dict[str, Any]
    scope: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_data")
    confidence: int
    usage_count: int
    last_used_at: datetime | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RetrievedCaseMemory(BaseModel):
    id: UUID
    memory_type: CaseMemoryType
    memory_key: str | None
    content: str
    metadata: dict[str, Any]
    relevance_score: float


class RetrievedUserPreference(BaseModel):
    id: UUID
    preference_type: UserPreferenceType
    preference_key: str
    preference_value: dict[str, Any]
    scope: str
    confidence: int
    relevance_score: float


class PlanningMemoryContext(BaseModel):
    """Compact, ranked memory supplied to a planner; never a full memory dump."""

    case_memories: list[RetrievedCaseMemory] = Field(default_factory=list)
    user_preferences: list[RetrievedUserPreference] = Field(default_factory=list)
