"""Analysis worker: turns research findings into reviewable observations."""

from src.api.schemas.planner import PlanStepType
from src.api.schemas.workers import (
    AnalysisFinding,
    AnalysisWorkerInput,
    AnalysisWorkerOutput,
)
from src.api.services.workers.base import require_step_type


class AnalysisWorker:
    """Produces structured observations only; it never invokes research or writing workers."""

    def run(self, worker_input: AnalysisWorkerInput) -> AnalysisWorkerOutput:
        require_step_type(worker_input.task, (PlanStepType.ANALYZE,))
        findings = [
            AnalysisFinding(
                finding_id=f"finding-{index}",
                observation=finding.summary,
                source_ids=[finding.source_id],
            )
            for index, finding in enumerate(worker_input.research_findings, start=1)
        ]
        return AnalysisWorkerOutput(
            task_id=worker_input.task.task_id,
            plan_id=worker_input.task.plan_id,
            findings=findings,
        )
