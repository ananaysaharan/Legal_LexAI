import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api.schemas.generated_documents import (
    GeneratedDocumentCreate,
    GeneratedDocumentType,
)
from src.api.services.generated_documents import GeneratedDocumentService


class FakeExecutionEngine:
    async def execute(self, **kwargs):
        return SimpleNamespace(
            execution_id=uuid4(),
            status="completed",
            workflow=SimpleNamespace(
                final_response=SimpleNamespace(
                    content="Draft response content", source_ids=["chunk-1"], review_passed=True, requires_human_review=True
                )
            ),
        )


class GeneratedDocumentTests(unittest.IsolatedAsyncioTestCase):
    async def test_creates_a_versioned_case_artifact_from_a_completed_execution(self) -> None:
        db = SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(scalar_one=lambda: 2)),
            add=lambda record: setattr(db, "record", record),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        request = GeneratedDocumentCreate(
            case_id=uuid4(),
            document_type=GeneratedDocumentType.RESPONSE_LETTER,
            title="Counterparty response",
            instructions="Draft a concise response based on the case record.",
            metadata={"audience": "counterparty"},
        )
        with patch(
            "src.api.services.generated_documents.CaseService.get_case_by_id",
            new=AsyncMock(),
        ):
            result = await GeneratedDocumentService(FakeExecutionEngine()).generate(
                db, "user-1", request
            )

        self.assertIs(result, db.record)
        self.assertEqual(result.version, 3)
        self.assertEqual(result.document_type, "response_letter")
        self.assertEqual(result.content, "Draft response content")
        self.assertEqual(result.citations_data, ["chunk-1"])
        self.assertEqual(result.metadata_data["audience"], "counterparty")
        db.commit.assert_awaited_once()

    def test_generation_request_preserves_document_type_and_instructions(self) -> None:
        request = GeneratedDocumentCreate(
            case_id=uuid4(),
            document_type=GeneratedDocumentType.INTERNAL_LEGAL_NOTE,
            title="Risk note",
            instructions="Highlight unresolved liability issues.",
        )
        prompt = GeneratedDocumentService._generation_request(request)
        self.assertIn("internal legal note", prompt)
        self.assertIn("Highlight unresolved liability issues.", prompt)


if __name__ == "__main__":
    unittest.main()
