"""Direct worker endpoints. They execute one worker only and do not orchestrate handoffs."""

from fastapi import APIRouter, Depends

from src.api.core.security import get_current_user
from src.api.schemas.workers import (
    AnalysisWorkerInput,
    AnalysisWorkerOutput,
    ResearchWorkerInput,
    ResearchWorkerOutput,
    ReviewerWorkerInput,
    ReviewerWorkerOutput,
    WriterWorkerInput,
    WriterWorkerOutput,
)
from src.api.services.workers.analysis import AnalysisWorker
from src.api.services.workers.research import ResearchWorker
from src.api.services.workers.reviewer import ReviewerWorker
from src.api.services.workers.writer import WriterWorker


router = APIRouter()


@router.post("/research", response_model=ResearchWorkerOutput)
async def run_research_worker(
    worker_input: ResearchWorkerInput,
    _current_user: dict = Depends(get_current_user),
) -> ResearchWorkerOutput:
    return ResearchWorker().run(worker_input)


@router.post("/analysis", response_model=AnalysisWorkerOutput)
async def run_analysis_worker(
    worker_input: AnalysisWorkerInput,
    _current_user: dict = Depends(get_current_user),
) -> AnalysisWorkerOutput:
    return AnalysisWorker().run(worker_input)


@router.post("/writer", response_model=WriterWorkerOutput)
async def run_writer_worker(
    worker_input: WriterWorkerInput,
    _current_user: dict = Depends(get_current_user),
) -> WriterWorkerOutput:
    return WriterWorker().run(worker_input)


@router.post("/reviewer", response_model=ReviewerWorkerOutput)
async def run_reviewer_worker(
    worker_input: ReviewerWorkerInput,
    _current_user: dict = Depends(get_current_user),
) -> ReviewerWorkerOutput:
    return ReviewerWorker().run(worker_input)
