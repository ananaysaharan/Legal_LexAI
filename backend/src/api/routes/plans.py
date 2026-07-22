from fastapi import APIRouter, Depends

from src.api.core.security import get_current_user
from src.api.schemas.planner import ExecutionPlan, PlanRequest
from src.api.services.planner import RuleBasedPlanner


router = APIRouter()
planner = RuleBasedPlanner()


@router.post("", response_model=ExecutionPlan)
async def create_plan(
    request: PlanRequest,
    _current_user: dict = Depends(get_current_user),
) -> ExecutionPlan:
    """Create a declarative plan. This endpoint does not execute any plan step."""
    return planner.create_plan(request.intent)
