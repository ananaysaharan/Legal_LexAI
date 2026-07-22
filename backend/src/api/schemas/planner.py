from enum import Enum
from typing import List, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.api.schemas.intent import Intent


class PlanStepType(str, Enum):
    RETRIEVE = "retrieve"
    ANALYZE = "analyze"
    RESEARCH = "research"
    GENERATE = "generate"
    REVIEW = "review"


class PlanStep(BaseModel):
    step_id: str
    step_type: PlanStepType
    description: str
    inputs: List[str]
    expected_output: str
    depends_on: List[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    intent: Intent


class ExecutionPlan(BaseModel):
    """A declarative work plan. It deliberately contains no execution results."""

    plan_id: UUID = Field(default_factory=uuid4)
    schema_version: Literal["execution_plan_v1"] = "execution_plan_v1"
    status: Literal["planned"] = "planned"
    planner: Literal["rule_based"] = "rule_based"
    prompt_template_version: str
    intent: Intent
    steps: List[PlanStep] = Field(min_length=1)
