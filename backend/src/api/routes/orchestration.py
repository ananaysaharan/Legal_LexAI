from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.security import get_current_user
from src.api.db.database import get_db
from src.api.schemas.orchestration import OrchestrationRequest, OrchestrationResponse
from src.api.services.orchestration import LegalWorkflow

router = APIRouter()
workflow = LegalWorkflow()


@router.post("/run", response_model=OrchestrationResponse)
async def run_workflow(
    request: OrchestrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> OrchestrationResponse:
    result = await workflow.run(
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
