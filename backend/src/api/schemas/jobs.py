from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobType(str, Enum):
    DOCUMENT_EXPORT = "document_export"
    DOCUMENT_PIPELINE = "document_pipeline"
    AI_DOCUMENT_GENERATION = "ai_document_generation"
    MEMORY_UPDATE = "memory_update"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobResponse(BaseModel):
    id: UUID
    case_id: UUID | None
    job_type: JobType
    status: JobStatus
    payload: dict[str, Any] = Field(validation_alias="payload_data")
    result: dict[str, Any] | None = Field(default=None, validation_alias="result_data")
    error: dict[str, Any] | None = Field(default=None, validation_alias="error_data")
    attempt_count: int

    model_config = ConfigDict(from_attributes=True)
