"""Celery entry points. Each task updates its durable BackgroundJob record."""

import asyncio
from uuid import UUID

from src.api.config import settings
from src.api.db.database import async_session_maker
from src.api.db.models import AIExecution
from src.api.schemas.exporting import ExportFormat
from src.api.schemas.generated_documents import GeneratedDocumentCreate
from src.api.schemas.orchestration import OrchestrationResponse
from src.api.services.exporting import DocumentExportService
from src.api.services.generated_documents import GeneratedDocumentService
from src.api.services.jobs import JobService
from src.api.services.memory_manager import MemoryManager
from src.api.services.pipeline import DocumentPipelineService
from src.api.services.storage import storage_service
from src.api.tasks.celery_app import celery_app


async def _run_export(job_id: UUID) -> None:
    async with async_session_maker() as db:
        job = await JobService.mark_running(db, job_id)
        if job is None:
            return
        result = await DocumentExportService().export(
            db,
            UUID(job.payload_data["document_id"]),
            ExportFormat(job.payload_data["format"]),
            bool(job.payload_data.get("include_citations", True)),
        )
        await JobService.mark_succeeded(db, job_id, result)


async def _run_document_generation(job_id: UUID) -> None:
    async with async_session_maker() as db:
        job = await JobService.mark_running(db, job_id)
        if job is None:
            return
        document = await GeneratedDocumentService().generate(
            db, job.user_id, GeneratedDocumentCreate.model_validate(job.payload_data["request"])
        )
        await JobService.mark_succeeded(db, job_id, {"document_id": str(document.id), "version": document.version})


async def _run_document_pipeline(job_id: UUID) -> None:
    async with async_session_maker() as db:
        job = await JobService.mark_running(db, job_id)
        if job is None:
            return
        document_id = UUID(job.payload_data["document_id"])
        file_bytes = await storage_service.download_file(job.payload_data["storage_path"])
        await DocumentPipelineService.process_document(db, document_id, file_bytes)
        await JobService.mark_succeeded(db, job_id, {"document_id": str(document_id), "processed": True})


async def _run_memory_update(job_id: UUID) -> None:
    async with async_session_maker() as db:
        job = await JobService.mark_running(db, job_id)
        if job is None:
            return
        execution = await db.get(AIExecution, UUID(job.payload_data["execution_id"]))
        if execution is None:
            raise ValueError("Execution not found")
        workflow = OrchestrationResponse.model_validate(
            {
                "status": execution.status,
                "trace": execution.trace_data,
                "intent": execution.intent_data,
                "plan": execution.plan_data,
                "final_response": execution.result_data,
                "error": execution.error_data,
            }
        )
        await MemoryManager().record_execution(db, execution, workflow)
        await JobService.mark_succeeded(db, job_id, {"execution_id": str(execution.id)})


def _execute_with_retry(task, job_id: str, runner) -> None:
    try:
        asyncio.run(runner(UUID(job_id)))
    except Exception as exc:
        error_message = str(exc) or "Task failed"
        if task.request.retries < settings.task_max_retries:
            raise task.retry(exc=exc, countdown=min(60, 2 ** task.request.retries))

        async def fail() -> None:
            async with async_session_maker() as db:
                await JobService.mark_failed(db, UUID(job_id), {"message": error_message})

        asyncio.run(fail())
        raise


@celery_app.task(bind=True, name="legal_ai.export_document")
def export_document_task(self, job_id: str) -> None:
    _execute_with_retry(self, job_id, _run_export)


@celery_app.task(bind=True, name="legal_ai.generate_document")
def generate_document_task(self, job_id: str) -> None:
    _execute_with_retry(self, job_id, _run_document_generation)


@celery_app.task(bind=True, name="legal_ai.process_document")
def process_document_task(self, job_id: str) -> None:
    _execute_with_retry(self, job_id, _run_document_pipeline)


@celery_app.task(bind=True, name="legal_ai.update_memory")
def update_memory_task(self, job_id: str) -> None:
    _execute_with_retry(self, job_id, _run_memory_update)
