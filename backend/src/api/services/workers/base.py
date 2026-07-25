"""Shared validation utilities for workers; this module does not coordinate workers."""

from typing import Iterable

from src.api.schemas.planner import PlanStepType
from src.api.schemas.workers import WorkerTask


def require_step_type(task: WorkerTask, allowed: Iterable[PlanStepType]) -> None:
    if task.step.step_type not in set(allowed):
        allowed_types = ", ".join(step_type.value for step_type in allowed)
        raise ValueError(
            f"Worker cannot process '{task.step.step_type.value}' steps; expected: {allowed_types}"
        )
