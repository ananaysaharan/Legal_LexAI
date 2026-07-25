"""Creates versioned legal artifacts from completed AI executions."""

import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import GeneratedDocument
from src.api.schemas.generated_documents import GeneratedDocumentCreate
from src.api.services.cases import CaseService
from src.api.services.execution_engine import AIExecutionEngine


class GeneratedDocumentService:
    """Artifact service: generation provenance and versioning stay outside chat storage."""

    def __init__(self, engine: AIExecutionEngine | None = None) -> None:
        self._engine = engine or AIExecutionEngine()

    async def generate(
        self, db: AsyncSession, user_id: str, request: GeneratedDocumentCreate
    ) -> GeneratedDocument:
        await CaseService.get_case_by_id(db, request.case_id, user_id)
        execution = await self._engine.execute(
            db=db,
            case_id=request.case_id,
            user_id=user_id,
            request=self._generation_request(request),
            top_k=request.top_k,
        )
        if execution.status != "completed" or not execution.workflow.final_response:
            raise ValueError("Document generation did not produce a reviewed result")

        document_key = request.document_key or self._key_from_title(request.title)
        version = await self._next_version(db, request.case_id, document_key)
        document = GeneratedDocument(
            case_id=request.case_id,
            source_execution_id=execution.execution_id,
            document_type=request.document_type.value,
            title=request.title,
            document_key=document_key,
            content=execution.workflow.final_response.content,
            version=version,
            status="draft",
            edit_operation="generate",
            edit_instructions=request.instructions,
            metadata_data={
                **request.metadata,
                "review_passed": execution.workflow.final_response.review_passed,
                "requires_human_review": execution.workflow.final_response.requires_human_review,
            },
            citations_data=execution.workflow.final_response.source_ids,
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    async def list_for_case(
        self, db: AsyncSession, case_id: UUID, user_id: str
    ) -> list[GeneratedDocument]:
        await CaseService.get_case_by_id(db, case_id, user_id)
        result = await db.execute(
            select(GeneratedDocument)
            .where(GeneratedDocument.case_id == case_id)
            .order_by(GeneratedDocument.updated_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def _generation_request(request: GeneratedDocumentCreate) -> str:
        return (
            f"Create a {request.document_type.value.replace('_', ' ')} titled "
            f"'{request.title}'. {request.instructions}"
        )

    @staticmethod
    def _key_from_title(title: str) -> str:
        key = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        return key[:255] or "generated-document"

    @staticmethod
    async def _next_version(
        db: AsyncSession, case_id: UUID, document_key: str
    ) -> int:
        result = await db.execute(
            select(func.max(GeneratedDocument.version)).where(
                GeneratedDocument.case_id == case_id,
                GeneratedDocument.document_key == document_key,
            )
        )
        return (result.scalar_one() or 0) + 1
