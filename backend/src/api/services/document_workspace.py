"""Immutable version workspace and AI editing pipeline for generated documents."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import GeneratedDocument
from src.api.schemas.generated_documents import (
    DocumentEditRequest,
    DocumentExportMetadata,
    DocumentSaveRequest,
)
from src.api.services.cases import CaseService
from src.api.services.execution_engine import AIExecutionEngine
from src.api.services.generated_documents import GeneratedDocumentService


class DocumentWorkspaceService:
    """Creates new document nodes for edits; existing versions are never mutated."""

    def __init__(self, engine: AIExecutionEngine | None = None) -> None:
        self._engine = engine or AIExecutionEngine()

    async def get_document(
        self, db: AsyncSession, document_id: UUID, user_id: str, include_deleted: bool = False
    ) -> GeneratedDocument:
        result = await db.execute(
            select(GeneratedDocument).where(GeneratedDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated document not found")
        await CaseService.get_case_by_id(db, document.case_id, user_id)
        if document.deleted_at is not None and not include_deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated document not found")
        return document

    async def edit_with_ai(
        self, db: AsyncSession, document_id: UUID, user_id: str, edit: DocumentEditRequest
    ) -> GeneratedDocument:
        source = await self.get_document(db, document_id, user_id)
        execution = await self._engine.execute(
            db=db,
            case_id=source.case_id,
            user_id=user_id,
            request=(
                f"{edit.operation.value.title()} the following generated legal document. "
                f"Instructions: {edit.instructions}\n\nDocument:\n{source.content}"
            ),
            top_k=edit.top_k,
        )
        if execution.status != "completed" or not execution.workflow.final_response:
            raise ValueError("AI edit did not produce a reviewed result")
        return await self._create_version(
            db, source, execution.workflow.final_response.content,
            operation=edit.operation.value, instructions=edit.instructions,
            source_execution_id=execution.execution_id,
            citations=execution.workflow.final_response.source_ids,
        )

    async def save_edit(
        self, db: AsyncSession, document_id: UUID, user_id: str, edit: DocumentSaveRequest
    ) -> GeneratedDocument:
        source = await self.get_document(db, document_id, user_id)
        return await self._create_version(
            db, source, edit.content, operation="manual_edit", instructions=edit.instructions,
            source_execution_id=None, citations=source.citations_data,
        )

    async def list_versions(
        self, db: AsyncSession, document_id: UUID, user_id: str, include_deleted: bool = False
    ) -> list[GeneratedDocument]:
        source = await self.get_document(db, document_id, user_id, include_deleted=True)
        statement = select(GeneratedDocument).where(
            GeneratedDocument.case_id == source.case_id,
            GeneratedDocument.document_key == source.document_key,
        )
        if not include_deleted:
            statement = statement.where(GeneratedDocument.deleted_at.is_(None))
        result = await db.execute(statement.order_by(GeneratedDocument.version.desc()))
        return list(result.scalars().all())

    async def restore(
        self, db: AsyncSession, document_id: UUID, user_id: str
    ) -> GeneratedDocument:
        source = await self.get_document(db, document_id, user_id, include_deleted=True)
        return await self._create_version(
            db, source, source.content, operation="restore",
            instructions=f"Restored from version {source.version}.",
            source_execution_id=None, citations=source.citations_data,
        )

    async def soft_delete(self, db: AsyncSession, document_id: UUID, user_id: str) -> None:
        document = await self.get_document(db, document_id, user_id)
        document.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        await db.commit()

    async def export_metadata(
        self, db: AsyncSession, document_id: UUID, user_id: str
    ) -> DocumentExportMetadata:
        document = await self.get_document(db, document_id, user_id, include_deleted=True)
        return DocumentExportMetadata(
            document_id=document.id,
            title=document.title,
            document_type=document.document_type,
            version=document.version,
            status=document.status,
            source_execution_id=document.source_execution_id,
            parent_document_id=document.parent_document_id,
            edit_operation=document.edit_operation,
            edit_instructions=document.edit_instructions,
            citations=document.citations_data,
            metadata=document.metadata_data,
        )

    async def _create_version(
        self, db: AsyncSession, source: GeneratedDocument, content: str,
        operation: str, instructions: str | None, source_execution_id: UUID | None,
        citations: list[str],
    ) -> GeneratedDocument:
        version = await GeneratedDocumentService._next_version(db, source.case_id, source.document_key)
        document = GeneratedDocument(
            case_id=source.case_id,
            source_execution_id=source_execution_id,
            parent_document_id=source.id,
            document_type=source.document_type,
            title=source.title,
            document_key=source.document_key,
            content=content,
            version=version,
            status="draft",
            edit_operation=operation,
            edit_instructions=instructions,
            metadata_data={**(source.metadata_data or {}), "parent_version": source.version},
            citations_data=citations,
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document
