from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.security import get_current_user
from src.api.db.database import get_db
from src.api.schemas.execution import AIExecutionRequest, AIExecutionResponse
from src.api.services.execution_engine import AIExecutionEngine

router = APIRouter()
engine = AIExecutionEngine()


@router.post("/execute", response_model=AIExecutionResponse)
async def execute_ai_request(
    request: AIExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> AIExecutionResponse:
    result = await engine.execute(
        db=db,
        case_id=request.case_id,
        user_id=current_user["sub"],
        request=request.request,
        top_k=request.top_k,
    )
    if result.status == "failed":
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=result.model_dump(mode="json"),
        )
    return result
