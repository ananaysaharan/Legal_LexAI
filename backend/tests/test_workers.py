import unittest
from uuid import uuid4

from src.api.schemas.intent import Intent, IntentType
from src.api.schemas.planner import PlanStep, PlanStepType
from src.api.schemas.workers import (
    AnalysisWorkerInput,
    EvidenceItem,
    ResearchWorkerInput,
    ReviewerWorkerInput,
    WorkerTask,
    WriterWorkerInput,
)
from src.api.services.workers.analysis import AnalysisWorker
from src.api.services.workers.research import ResearchWorker
from src.api.services.workers.reviewer import ReviewerWorker
from src.api.services.workers.writer import WriterWorker


def task(step_type: PlanStepType) -> WorkerTask:
    return WorkerTask(
        plan_id=uuid4(),
        intent=Intent(
            task_type=IntentType.CONTRACT_REVIEW,
            confidence=0.95,
            normalized_request="Review this contract.",
            matched_signals=["Review"],
        ),
        step=PlanStep(
            step_id=step_type.value,
            step_type=step_type,
            description="Test step",
            inputs=[],
            expected_output="Test output",
        ),
    )


class WorkerTests(unittest.TestCase):
    def test_workers_have_structured_independent_handoffs(self) -> None:
        research_task = task(PlanStepType.RETRIEVE)
        research = ResearchWorker().run(ResearchWorkerInput(
            task=research_task,
            sources=[EvidenceItem(source_id="chunk-1", document_name="agreement.pdf", page_number=2, content="  Liability is capped.  ")],
        ))
        self.assertEqual(research.findings[0].summary, "Liability is capped.")

        analysis_task = task(PlanStepType.ANALYZE)
        analysis = AnalysisWorker().run(AnalysisWorkerInput(task=analysis_task, research_findings=research.findings))
        self.assertEqual(analysis.findings[0].source_ids, ["chunk-1"])

        writer_task = task(PlanStepType.GENERATE)
        writer = WriterWorker().run(WriterWorkerInput(task=writer_task, findings=analysis.findings, title="Review draft"))
        self.assertIn("Liability is capped.", writer.draft.content)

        reviewer_task = task(PlanStepType.REVIEW)
        review = ReviewerWorker().run(ReviewerWorkerInput(task=reviewer_task, draft=writer.draft, available_source_ids=["chunk-1"]))
        self.assertTrue(all(check.passed for check in review.checks))
        self.assertTrue(review.requires_human_review)

    def test_worker_rejects_an_incompatible_plan_step(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot process"):
            ResearchWorker().run(ResearchWorkerInput(task=task(PlanStepType.REVIEW), sources=[]))


if __name__ == "__main__":
    unittest.main()
