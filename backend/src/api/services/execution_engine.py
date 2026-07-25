"""Single entry point for executing, recording, and returning AI workflows."""

from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import AIExecution
from src.api.schemas.execution import AIExecutionResponse
from src.api.schemas.orchestration import OrchestrationFailure, OrchestrationResponse
from src.api.services.cases import CaseService
from src.api.services.memory_manager import MemoryManager
from src.api.services.orchestration import LegalWorkflow
from src.api.services.task_dispatcher import TaskDispatcher


class ExecutionRecordService:
    """Persistence boundary for workflow metadata used by future memory and evaluation."""

    @staticmethod
    async def save(
        db: AsyncSession,
        case_id: UUID,
        user_id: str,
        request: str,
        workflow: OrchestrationResponse,
        duration_ms: int,
    ) -> AIExecution:
        execution = AIExecution(
            case_id=case_id,
            user_id=user_id,
            request_text=request,
            status=workflow.status,
            intent_data=(
                workflow.intent.model_dump(mode="json") if workflow.intent else None
            ),
            plan_data=workflow.plan.model_dump(mode="json") if workflow.plan else None,
            trace_data=workflow.trace,
            result_data=(
                workflow.final_response.model_dump(mode="json")
                if workflow.final_response
                else None
            ),
            error_data=(
                workflow.error.model_dump(mode="json") if workflow.error else None
            ),
            duration_ms=duration_ms,
            completed_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        return execution


class AIExecutionEngine:
    """Authorizes a request, runs LangGraph, and records the complete execution lifecycle."""

    def __init__(
        self,
        workflow: LegalWorkflow | None = None,
        memory_manager: MemoryManager | None = None,
        task_dispatcher: TaskDispatcher | None = None,
    ) -> None:
        self._workflow = workflow or LegalWorkflow()
        self._memory_manager = memory_manager
        self._task_dispatcher = task_dispatcher or TaskDispatcher()

    async def execute(
        self,
        db: AsyncSession,
        case_id: UUID,
        user_id: str,
        request: str,
        top_k: int = 5,
    ) -> AIExecutionResponse:
        # Authorize at the engine boundary before any intent, planning, or graph work.
        await CaseService.get_case_by_id(db, case_id, user_id)

        started_at = perf_counter()
        try:
            workflow_result = await self._workflow.run(
                db=db,
                case_id=case_id,
                user_id=user_id,
                request=request,
                top_k=top_k,
            )
        except Exception:
            workflow_result = OrchestrationResponse(
                status="failed",
                trace=["engine"],
                error=OrchestrationFailure(
                    node="engine", message="AI workflow could not be started"
                ),
            )

        duration_ms = int((perf_counter() - started_at) * 1_000)
        execution = await ExecutionRecordService.save(
            db=db,
            case_id=case_id,
            user_id=user_id,
            request=request,
            workflow=workflow_result,
            duration_ms=duration_ms,
        )
        try:
            if self._memory_manager is not None:
                await self._memory_manager.record_execution(db, execution, workflow_result)
            elif workflow_result.status == "completed":
                await self._task_dispatcher.enqueue_memory_update(
                    db, user_id, case_id, {"execution_id": str(execution.id)}
                )
        except Exception:
            # Background bookkeeping must not invalidate an otherwise successful execution.
            pass
        return AIExecutionResponse(
            execution_id=execution.id,
            status=workflow_result.status,
            workflow=workflow_result,
        )
