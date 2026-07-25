import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api.schemas.generated_documents import DocumentSaveRequest
from src.api.services.document_workspace import DocumentWorkspaceService


class DocumentWorkspaceTests(unittest.IsolatedAsyncioTestCase):
    async def test_manual_save_creates_an_immutable_child_version(self) -> None:
        case_id = uuid4()
        source = SimpleNamespace(
            id=uuid4(),
            case_id=case_id,
            document_type="response_letter",
            title="Response",
            document_key="response",
            content="Original draft",
            version=2,
            citations_data=["chunk-1"],
            metadata_data={"review_passed": True},
            deleted_at=None,
        )
        db = SimpleNamespace(
            execute=AsyncMock(side_effect=[
                SimpleNamespace(scalar_one_or_none=lambda: source),
                SimpleNamespace(scalar_one=lambda: 2),
            ]),
            add=lambda record: setattr(db, "record", record),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        with patch(
            "src.api.services.document_workspace.CaseService.get_case_by_id",
            new=AsyncMock(),
        ):
            saved = await DocumentWorkspaceService().save_edit(
                db, source.id, "user-1", DocumentSaveRequest(content="Updated draft", instructions="Clarify the deadline.")
            )

        self.assertIs(saved, db.record)
        self.assertEqual(source.content, "Original draft")
        self.assertEqual(saved.parent_document_id, source.id)
        self.assertEqual(saved.version, 3)
        self.assertEqual(saved.edit_operation, "manual_edit")
        self.assertEqual(saved.edit_instructions, "Clarify the deadline.")

    async def test_soft_delete_marks_the_version_without_deleting_it(self) -> None:
        source = SimpleNamespace(id=uuid4(), case_id=uuid4(), deleted_at=None)
        db = SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: source)),
            commit=AsyncMock(),
        )
        with patch(
            "src.api.services.document_workspace.CaseService.get_case_by_id",
            new=AsyncMock(),
        ):
            await DocumentWorkspaceService().soft_delete(db, source.id, "user-1")
        self.assertIsNotNone(source.deleted_at)
        db.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
