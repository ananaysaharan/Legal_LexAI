import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api.schemas.memory import PlanningMemoryContext
from src.api.services.memory_retrieval import MemoryRetrievalService


class MemoryRetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_only_ranked_case_memory_and_bounded_preferences(self) -> None:
        case_memories = [
            SimpleNamespace(
                id=uuid4(),
                memory_type="important_finding",
                memory_key="liability_cap",
                content="Liability is capped at fees paid.",
                metadata_data={},
            ),
            SimpleNamespace(
                id=uuid4(),
                memory_type="legal_entity",
                memory_key="supplier",
                content="Supplier is Acme Corp.",
                metadata_data={},
            ),
        ]
        preferences = [
            SimpleNamespace(
                id=uuid4(),
                preference_type="citation_preferences",
                preference_key="citations",
                preference_value={"include_pages": True},
                scope="global",
                confidence=90,
            ),
            SimpleNamespace(
                id=uuid4(),
                preference_type="frequently_used_task",
                preference_key="summaries",
                preference_value={"task": "summary"},
                scope="global",
                confidence=70,
            ),
        ]
        with (
            patch(
                "src.api.services.memory_retrieval.CaseMemoryQueryService.list_for_case",
                new=AsyncMock(return_value=case_memories),
            ),
            patch(
                "src.api.services.memory_retrieval.UserPreferenceMemoryQueryService.list_for_user",
                new=AsyncMock(return_value=preferences),
            ),
        ):
            context = await MemoryRetrievalService().retrieve_for_planning(
                SimpleNamespace(), uuid4(), "user-1", "Review the liability cap", case_limit=1, preference_limit=1
            )

        self.assertEqual(len(context.case_memories), 1)
        self.assertEqual(context.case_memories[0].memory_key, "liability_cap")
        self.assertEqual(len(context.user_preferences), 1)
        self.assertEqual(context.user_preferences[0].preference_key, "citations")

    async def test_returns_empty_context_when_no_memory_is_relevant(self) -> None:
        with (
            patch(
                "src.api.services.memory_retrieval.CaseMemoryQueryService.list_for_case",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "src.api.services.memory_retrieval.UserPreferenceMemoryQueryService.list_for_user",
                new=AsyncMock(return_value=[]),
            ),
        ):
            context = await MemoryRetrievalService().retrieve_for_planning(
                SimpleNamespace(), uuid4(), "user-1", "Review the liability cap"
            )
        self.assertEqual(context, PlanningMemoryContext())


if __name__ == "__main__":
    unittest.main()
