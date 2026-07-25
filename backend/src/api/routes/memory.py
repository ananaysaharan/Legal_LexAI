"""Memory storage endpoints only. Retrieval is intentionally not exposed here."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.security import get_current_user
from src.api.db.database import get_db
from src.api.schemas.memory import (
    CaseMemoryCreate,
    CaseMemoryResponse,
    CaseMemoryType,
    CaseMemoryUpdate,
    UserPreferenceMemoryResponse,
    UserPreferenceMemoryUpsert,
    UserPreferenceType,
)
from src.api.services.cases import CaseService
from src.api.services.memory_manager import MemoryManager
from src.api.services.memory_storage import (
    CaseMemoryQueryService,
    UserPreferenceMemoryQueryService,
)

router = APIRouter()
memory_manager = MemoryManager()


@router.post(
    "/cases/{case_id}",
    response_model=CaseMemoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def store_case_memory(
    case_id: UUID,
    memory: CaseMemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> CaseMemoryResponse:
    await CaseService.get_case_by_id(db, case_id, current_user["sub"])
    return await memory_manager.save_case_memory(db, case_id, memory)


@router.get("/cases/{case_id}", response_model=list[CaseMemoryResponse])
async def retrieve_case_memories(
    case_id: UUID,
    memory_type: CaseMemoryType | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[CaseMemoryResponse]:
    await CaseService.get_case_by_id(db, case_id, current_user["sub"])
    return await CaseMemoryQueryService.list_for_case(db, case_id, memory_type, limit)


@router.patch("/cases/{case_id}/{memory_id}", response_model=CaseMemoryResponse)
async def update_case_memory(
    case_id: UUID,
    memory_id: UUID,
    memory: CaseMemoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> CaseMemoryResponse:
    await CaseService.get_case_by_id(db, case_id, current_user["sub"])
    record = await memory_manager.update_case_memory(db, case_id, memory_id, memory)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case memory not found"
        )
    return record


@router.put("/preferences", response_model=UserPreferenceMemoryResponse)
async def upsert_user_preference_memory(
    preference: UserPreferenceMemoryUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> UserPreferenceMemoryResponse:
    return await memory_manager.save_user_preference(
        db, current_user["sub"], preference
    )


@router.get("/preferences", response_model=list[UserPreferenceMemoryResponse])
async def list_user_preference_memories(
    preference_type: UserPreferenceType | None = None,
    scope: str | None = Query(default=None, min_length=1, max_length=80),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[UserPreferenceMemoryResponse]:
    return await UserPreferenceMemoryQueryService.list_for_user(
        db, current_user["sub"], preference_type, scope, limit
    )
