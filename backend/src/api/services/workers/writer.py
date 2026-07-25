"""Writer worker: formats supplied findings into a draft without conducting analysis."""

from src.api.schemas.planner import PlanStepType
from src.api.schemas.workers import DraftDocument, WriterWorkerInput, WriterWorkerOutput
from src.api.services.workers.base import require_step_type


class WriterWorker:
    """Creates a deterministic draft from supplied findings; it does not call other workers."""

    def run(self, worker_input: WriterWorkerInput) -> WriterWorkerOutput:
        require_step_type(worker_input.task, (PlanStepType.GENERATE,))
        content = "\n\n".join(
            f"{index}. {finding.observation}"
            for index, finding in enumerate(worker_input.findings, start=1)
        )
        source_ids = list(
            dict.fromkeys(
                source_id
                for finding in worker_input.findings
                for source_id in finding.source_ids
            )
        )
        return WriterWorkerOutput(
            task_id=worker_input.task.task_id,
            plan_id=worker_input.task.plan_id,
            draft=DraftDocument(
                title=worker_input.title,
                content=content,
                source_ids=source_ids,
            ),
        )
