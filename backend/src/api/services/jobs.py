"""Durable job tracking separate from queue transport and task implementations."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import BackgroundJob
from src.api.schemas.jobs import JobStatus, JobType


class JobService:
    @staticmethod
    async def create(
        db: AsyncSession, user_id: str, job_type: JobType, payload: dict, case_id: UUID | None = None
    ) -> BackgroundJob:
        job = BackgroundJob(
            user_id=user_id, case_id=case_id, job_type=job_type.value,
            status=JobStatus.QUEUED.value, payload_data=payload,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def get_for_user(db: AsyncSession, job_id: UUID, user_id: str) -> BackgroundJob | None:
        result = await db.execute(
            select(BackgroundJob).where(BackgroundJob.id == job_id, BackgroundJob.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_running(db: AsyncSession, job_id: UUID) -> BackgroundJob | None:
        return await JobService._update_status(db, job_id, JobStatus.RUNNING, started_at=datetime.now(UTC).replace(tzinfo=None))

    @staticmethod
    async def mark_succeeded(db: AsyncSession, job_id: UUID, result: dict) -> BackgroundJob | None:
        return await JobService._update_status(db, job_id, JobStatus.SUCCEEDED, result_data=result, completed_at=datetime.now(UTC).replace(tzinfo=None))

    @staticmethod
    async def mark_failed(db: AsyncSession, job_id: UUID, error: dict) -> BackgroundJob | None:
        return await JobService._update_status(db, job_id, JobStatus.FAILED, error_data=error, completed_at=datetime.now(UTC).replace(tzinfo=None))

    @staticmethod
    async def set_task_id(db: AsyncSession, job_id: UUID, task_id: str) -> BackgroundJob | None:
        result = await db.execute(select(BackgroundJob).where(BackgroundJob.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            return None
        job.celery_task_id = task_id
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def _update_status(db: AsyncSession, job_id: UUID, status: JobStatus, **values) -> BackgroundJob | None:
        result = await db.execute(select(BackgroundJob).where(BackgroundJob.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            return None
        job.status = status.value
        for key, value in values.items():
            setattr(job, key, value)
        if status == JobStatus.RUNNING:
            job.attempt_count += 1
        await db.commit()
        await db.refresh(job)
        return job
