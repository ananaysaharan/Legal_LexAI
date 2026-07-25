"""Queue transport boundary. API services create durable jobs before dispatching."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.jobs import JobType
from src.api.services.jobs import JobService


class TaskDispatcher:
    async def enqueue_export(
        self, db: AsyncSession, user_id: str, case_id: UUID, payload: dict
    ):
        return await self._enqueue(db, user_id, case_id, JobType.DOCUMENT_EXPORT, payload, "legal_ai.export_document")

    async def enqueue_document_generation(
        self, db: AsyncSession, user_id: str, case_id: UUID, payload: dict
    ):
        return await self._enqueue(db, user_id, case_id, JobType.AI_DOCUMENT_GENERATION, payload, "legal_ai.generate_document")

    async def enqueue_document_pipeline(
        self, db: AsyncSession, user_id: str, case_id: UUID, payload: dict
    ):
        return await self._enqueue(db, user_id, case_id, JobType.DOCUMENT_PIPELINE, payload, "legal_ai.process_document")

    async def enqueue_memory_update(
        self, db: AsyncSession, user_id: str, case_id: UUID, payload: dict
    ):
        return await self._enqueue(db, user_id, case_id, JobType.MEMORY_UPDATE, payload, "legal_ai.update_memory")

    async def _enqueue(
        self, db: AsyncSession, user_id: str, case_id: UUID, job_type: JobType, payload: dict, task_name: str
    ):
        job = await JobService.create(db, user_id, job_type, payload, case_id)
        try:
            from src.api.tasks.celery_app import celery_app

            task = celery_app.send_task(task_name, args=[str(job.id)])
            await JobService.set_task_id(db, job.id, task.id)
            return job
        except Exception as exc:
            await JobService.mark_failed(db, job.id, {"message": f"Queue unavailable: {exc}"})
            return job
