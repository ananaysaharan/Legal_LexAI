"""Research worker: converts supplied evidence into structured research findings."""

from src.api.schemas.planner import PlanStepType
from src.api.schemas.workers import (
    ResearchFinding,
    ResearchWorkerInput,
    ResearchWorkerOutput,
)
from src.api.services.workers.base import require_step_type


class ResearchWorker:
    """Handles evidence organization only; it does not invoke analysis or other workers."""

    def run(self, worker_input: ResearchWorkerInput) -> ResearchWorkerOutput:
        require_step_type(
            worker_input.task, (PlanStepType.RETRIEVE, PlanStepType.RESEARCH)
        )
        findings = [
            ResearchFinding(
                source_id=source.source_id,
                summary=" ".join(source.content.split()),
                document_name=source.document_name,
                page_number=source.page_number,
            )
            for source in worker_input.sources
        ]
        return ResearchWorkerOutput(
            task_id=worker_input.task.task_id,
            plan_id=worker_input.task.plan_id,
            findings=findings,
        )
