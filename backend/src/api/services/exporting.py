"""Export orchestration: authorization, artifact generation, and object storage."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import Case, GeneratedDocument
from src.api.schemas.exporting import ExportFormat
from src.api.services.exporters import ExportContext, ExporterRegistry
from src.api.services.storage import storage_service


class DocumentExportService:
    def __init__(self, registry: ExporterRegistry | None = None) -> None:
        self._registry = registry or ExporterRegistry()

    async def export(
        self, db: AsyncSession, document_id: UUID, export_format: ExportFormat, include_citations: bool
    ) -> dict:
        document = await db.get(GeneratedDocument, document_id)
        if document is None or document.deleted_at is not None:
            raise ValueError("Generated document not found")
        case = await db.get(Case, document.case_id)
        if case is None:
            raise ValueError("Case not found")
        artifact = self._registry.get(export_format).export(
            ExportContext(document=document, case=case, include_citations=include_citations)
        )
        storage_path = f"exports/{case.id}/{document.id}/{artifact.filename}"
        await storage_service.upload_file(artifact.content, storage_path, artifact.content_type)
        return {
            "storage_path": storage_path,
            "filename": artifact.filename,
            "content_type": artifact.content_type,
            "size_bytes": len(artifact.content),
            "document_id": str(document.id),
            "version": document.version,
        }
