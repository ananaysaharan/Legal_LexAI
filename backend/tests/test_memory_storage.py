import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from src.api.schemas.memory import (
    CaseMemoryCreate,
    CaseMemoryType,
    CaseMemoryUpdate,
    PreferenceUpdateStrategy,
    UserPreferenceMemoryUpsert,
    UserPreferenceType,
)
from src.api.services.memory_storage import (
    CaseMemoryQueryService,
    CaseMemoryStorageService,
    UserPreferenceMemoryStorageService,
)


class MemoryStorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_stores_case_memory_with_provenance_without_retrieval(self) -> None:
        db = SimpleNamespace(
            add=lambda record: setattr(db, "record", record),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        memory = await CaseMemoryStorageService.store(
            db,
            uuid4(),
            CaseMemoryCreate(
                memory_type=CaseMemoryType.IMPORTANT_FINDING,
                memory_key="governing_law",
                content="The agreement selects New York law.",
                metadata={"confidence": "high"},
                source_execution_id=uuid4(),
            ),
        )
        self.assertEqual(memory.memory_type, "important_finding")
        self.assertEqual(memory.metadata_data, {"confidence": "high"})
        db.commit.assert_awaited_once()

    async def test_lists_and_updates_only_memories_belonging_to_the_case(self) -> None:
        record = SimpleNamespace(
            id=uuid4(),
            case_id=uuid4(),
            content="Original summary",
            memory_key="initial",
            metadata_data={},
            source_execution_id=None,
            source_document_id=None,
            source_conversation_id=None,
        )
        list_result = SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=lambda: [record])
        )
        update_result = SimpleNamespace(scalar_one_or_none=lambda: record)
        db = SimpleNamespace(
            execute=AsyncMock(side_effect=[list_result, update_result]),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        memories = await CaseMemoryQueryService.list_for_case(
            db, record.case_id, CaseMemoryType.CONVERSATION_SUMMARY
        )
        updated = await CaseMemoryQueryService.update(
            db,
            record.case_id,
            record.id,
            CaseMemoryUpdate(content="Updated summary", metadata={"curated": True}),
        )
        self.assertEqual(memories, [record])
        self.assertEqual(updated.content, "Updated summary")
        self.assertEqual(updated.metadata_data, {"curated": True})

    async def test_upserts_cross_case_user_preference(self) -> None:
        record = SimpleNamespace(
            preference_value=None,
            metadata_data=None,
            preference_type=None,
            confidence=None,
            usage_count=0,
            last_used_at=None,
            is_active=False,
        )
        query_result = SimpleNamespace(scalar_one_or_none=lambda: record)
        db = SimpleNamespace(
            execute=AsyncMock(return_value=query_result),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        preference = UserPreferenceMemoryUpsert(
            preference_type=UserPreferenceType.CITATION_PREFERENCES,
            preference_key="citation_style",
            preference_value={"format": "bluebook"},
        )
        result = await UserPreferenceMemoryStorageService.upsert(
            db, "user-1", preference
        )
        self.assertIs(result, record)
        self.assertEqual(record.preference_value, {"format": "bluebook"})
        self.assertEqual(record.preference_type, "citation_preferences")
        db.commit.assert_awaited_once()

    async def test_merges_preferences_and_tracks_usage_without_chat_data(self) -> None:
        record = SimpleNamespace(
            preference_value={"format": "bluebook"},
            metadata_data={"source": "explicit"},
            preference_type="citation_preferences",
            confidence=80,
            usage_count=2,
            last_used_at=None,
            is_active=False,
        )
        query_result = SimpleNamespace(scalar_one_or_none=lambda: record)
        db = SimpleNamespace(
            execute=AsyncMock(return_value=query_result),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        merged = await UserPreferenceMemoryStorageService.upsert(
            db,
            "user-1",
            UserPreferenceMemoryUpsert(
                preference_type=UserPreferenceType.CITATION_PREFERENCES,
                preference_key="citation_style",
                preference_value={"include_page_numbers": True},
                metadata={"updated_by": "user"},
                confidence=95,
                update_strategy=PreferenceUpdateStrategy.MERGE,
            ),
        )
        self.assertIs(merged, record)
        self.assertEqual(
            record.preference_value,
            {"format": "bluebook", "include_page_numbers": True},
        )
        self.assertEqual(
            record.metadata_data,
            {"source": "explicit", "updated_by": "user"},
        )
        self.assertTrue(record.is_active)

        await UserPreferenceMemoryStorageService.upsert(
            db,
            "user-1",
            UserPreferenceMemoryUpsert(
                preference_type=UserPreferenceType.CITATION_PREFERENCES,
                preference_key="citation_style",
                preference_value={},
                update_strategy=PreferenceUpdateStrategy.INCREMENT_USAGE,
            ),
        )
        self.assertEqual(record.usage_count, 3)

    def test_rejects_conversation_payloads_in_user_preferences(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not store conversations"):
            UserPreferenceMemoryUpsert(
                preference_type=UserPreferenceType.WRITING_STYLE,
                preference_key="tone",
                preference_value={"chat_history": "raw transcript"},
            )


if __name__ == "__main__":
    unittest.main()
