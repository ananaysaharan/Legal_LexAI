from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.security import get_current_user
from src.api.db.database import get_db
from src.api.schemas.jobs import JobResponse
from src.api.services.jobs import JobService

router = APIRouter()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> JobResponse:
    job = await JobService.get_for_user(db, job_id, current_user["sub"])
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job
