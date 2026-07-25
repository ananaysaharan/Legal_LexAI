"""Reviewer worker: checks draft completeness and evidence references."""

from src.api.schemas.planner import PlanStepType
from src.api.schemas.workers import ReviewCheck, ReviewerWorkerInput, ReviewerWorkerOutput
from src.api.services.workers.base import require_step_type


class ReviewerWorker:
    """Evaluates supplied drafts only; it does not rewrite or invoke other workers."""

    def run(self, worker_input: ReviewerWorkerInput) -> ReviewerWorkerOutput:
        require_step_type(worker_input.task, (PlanStepType.REVIEW,))
        available_sources = set(worker_input.available_source_ids)
        cited_sources = set(worker_input.draft.source_ids)
        checks = [
            ReviewCheck(
                name="non_empty_draft",
                passed=bool(worker_input.draft.content.strip()),
                detail="Draft contains content." if worker_input.draft.content.strip() else "Draft is empty.",
            ),
            ReviewCheck(
                name="source_references",
                passed=bool(cited_sources) and cited_sources.issubset(available_sources),
                detail="All draft sources are available." if cited_sources and cited_sources.issubset(available_sources) else "Draft has missing or unavailable source references.",
            ),
        ]
        return ReviewerWorkerOutput(
            task_id=worker_input.task.task_id,
            plan_id=worker_input.task.plan_id,
            checks=checks,
        )
