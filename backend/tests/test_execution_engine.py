import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api.schemas.orchestration import FinalResponse, OrchestrationResponse
from src.api.services.execution_engine import AIExecutionEngine


class FakeWorkflow:
    async def run(self, **kwargs):
        return OrchestrationResponse(
            status="completed",
            trace=["intent", "planner", "finalize"],
            final_response=FinalResponse(
                content="Grounded result", source_ids=["chunk-1"], review_passed=True
            ),
        )


class FailingWorkflow:
    async def run(self, **kwargs):
        raise RuntimeError("Unexpected failure")


class ExecutionEngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_executes_workflow_and_persists_complete_metadata(self) -> None:
        execution = SimpleNamespace(id=uuid4())
        db = SimpleNamespace()
        memory_manager = SimpleNamespace(record_execution=AsyncMock())
        with (
            patch(
                "src.api.services.execution_engine.CaseService.get_case_by_id",
                new=AsyncMock(),
            ) as authorize,
            patch(
                "src.api.services.execution_engine.ExecutionRecordService.save",
                new=AsyncMock(return_value=execution),
            ) as save,
        ):
            result = await AIExecutionEngine(
                workflow=FakeWorkflow(), memory_manager=memory_manager
            ).execute(
                db=db,
                case_id=uuid4(),
                user_id="user-1",
                request="Review this contract.",
            )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.execution_id, execution.id)
        self.assertEqual(result.workflow.final_response.content, "Grounded result")
        authorize.assert_awaited_once()
        self.assertEqual(
            save.await_args.kwargs["workflow"].trace, ["intent", "planner", "finalize"]
        )
        memory_manager.record_execution.assert_awaited_once()

    async def test_records_engine_failures_as_structured_workflow_results(self) -> None:
        execution = SimpleNamespace(id=uuid4())
        with (
            patch(
                "src.api.services.execution_engine.CaseService.get_case_by_id",
                new=AsyncMock(),
            ),
            patch(
                "src.api.services.execution_engine.ExecutionRecordService.save",
                new=AsyncMock(return_value=execution),
            ) as save,
        ):
            result = await AIExecutionEngine(workflow=FailingWorkflow()).execute(
                db=SimpleNamespace(),
                case_id=uuid4(),
                user_id="user-1",
                request="Review this contract.",
            )

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.workflow.error.node, "engine")
        self.assertEqual(save.await_args.kwargs["workflow"].status, "failed")


if __name__ == "__main__":
    unittest.main()
