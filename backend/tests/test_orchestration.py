import unittest
from types import SimpleNamespace
from uuid import uuid4

from src.api.schemas.memory import PlanningMemoryContext
from src.api.schemas.search import SearchResultChunk
from src.api.services.orchestration import LegalWorkflow


class FakeRetriever:
    async def retrieve(self, db, case_id, user_id, query, top_k):
        return [SearchResultChunk(chunk_id=uuid4(), document_id=uuid4(), document_filename="agreement.pdf", page_number=3, chunk_index=0, text_content="Liability is capped at fees paid in the prior 12 months.", similarity_score=0.9)]


class FailingRetriever:
    async def retrieve(self, *args, **kwargs):
        raise RuntimeError("Vector search unavailable")


class FakeMemoryRetriever:
    async def retrieve_for_planning(self, *args, **kwargs):
        return PlanningMemoryContext()


class OrchestrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_graph_runs_each_node_and_returns_final_response(self) -> None:
        result = await LegalWorkflow(
            retriever=FakeRetriever(), memory_retriever=FakeMemoryRetriever()
        ).run(db=SimpleNamespace(), case_id=uuid4(), user_id="user-1", request="Review this contract.")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.trace, ["intent", "memory", "planner", "research", "analysis", "writer", "reviewer", "finalize"])
        self.assertTrue(result.final_response.review_passed)
        self.assertIn("Liability is capped", result.final_response.content)

    async def test_graph_routes_node_failures_to_terminal_failure(self) -> None:
        result = await LegalWorkflow(
            retriever=FailingRetriever(), memory_retriever=FakeMemoryRetriever()
        ).run(db=SimpleNamespace(), case_id=uuid4(), user_id="user-1", request="Review this contract.")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error.node, "research")
        self.assertEqual(result.trace, ["intent", "memory", "planner", "research", "failure"])


if __name__ == "__main__":
    unittest.main()
