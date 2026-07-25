from enum import Enum
from typing import List, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.api.schemas.intent import Intent
from src.api.schemas.planner import PlanStep


class WorkerType(str, Enum):
    RESEARCH = "research"
    ANALYSIS = "analysis"
    WRITER = "writer"
    REVIEWER = "reviewer"


class WorkerTask(BaseModel):
    """Planner-derived metadata shared by all independent worker calls."""

    task_id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    intent: Intent
    step: PlanStep


class EvidenceItem(BaseModel):
    source_id: str
    document_name: str
    page_number: int
    content: str


class ResearchWorkerInput(BaseModel):
    task: WorkerTask
    sources: List[EvidenceItem]


class ResearchFinding(BaseModel):
    source_id: str
    summary: str
    document_name: str
    page_number: int


class ResearchWorkerOutput(BaseModel):
    task_id: UUID
    plan_id: UUID
    worker: Literal[WorkerType.RESEARCH] = WorkerType.RESEARCH
    findings: List[ResearchFinding]


class AnalysisWorkerInput(BaseModel):
    task: WorkerTask
    research_findings: List[ResearchFinding]


class AnalysisFinding(BaseModel):
    finding_id: str
    observation: str
    source_ids: List[str]
    requires_human_assessment: bool = True


class AnalysisWorkerOutput(BaseModel):
    task_id: UUID
    plan_id: UUID
    worker: Literal[WorkerType.ANALYSIS] = WorkerType.ANALYSIS
    findings: List[AnalysisFinding]


class WriterWorkerInput(BaseModel):
    task: WorkerTask
    findings: List[AnalysisFinding]
    title: str = "Draft"


class DraftDocument(BaseModel):
    title: str
    content: str
    source_ids: List[str]


class WriterWorkerOutput(BaseModel):
    task_id: UUID
    plan_id: UUID
    worker: Literal[WorkerType.WRITER] = WorkerType.WRITER
    draft: DraftDocument


class ReviewerWorkerInput(BaseModel):
    task: WorkerTask
    draft: DraftDocument
    available_source_ids: List[str]


class ReviewCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class ReviewerWorkerOutput(BaseModel):
    task_id: UUID
    plan_id: UUID
    worker: Literal[WorkerType.REVIEWER] = WorkerType.REVIEWER
    checks: List[ReviewCheck]
    requires_human_review: bool = True
