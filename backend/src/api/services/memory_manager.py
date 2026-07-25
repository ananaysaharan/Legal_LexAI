"""The single policy boundary for automatic memory persistence."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import AIExecution, CaseMemory, UserPreferenceMemory
from src.api.schemas.memory import (
    CaseMemoryCreate,
    CaseMemoryType,
    CaseMemoryUpdate,
    UserPreferenceMemoryUpsert,
)
from src.api.schemas.orchestration import OrchestrationResponse
from src.api.services.memory_storage import (
    CaseMemoryQueryService,
    CaseMemoryStorageService,
    UserPreferenceMemoryStorageService,
)


class MemoryManager:
    """Applies retention rules; planners, workers, and the engine do not write memory."""

    async def save_case_memory(
        self, db: AsyncSession, case_id: UUID, memory: CaseMemoryCreate
    ) -> CaseMemory:
        if memory.memory_key:
            existing = await self._find_case_memory(
                db, case_id, memory.memory_type, memory.memory_key
            )
            if existing is not None:
                updated = await CaseMemoryQueryService.update(
                    db,
                    case_id,
                    existing.id,
                    CaseMemoryUpdate(
                        content=memory.content,
                        metadata=memory.metadata,
                        source_execution_id=memory.source_execution_id,
                        source_document_id=memory.source_document_id,
                        source_conversation_id=memory.source_conversation_id,
                    ),
                )
                if updated is not None:
                    return updated
        return await CaseMemoryStorageService.store(db, case_id, memory)

    async def save_user_preference(
        self,
        db: AsyncSession,
        user_id: str,
        preference: UserPreferenceMemoryUpsert,
    ) -> UserPreferenceMemory:
        return await UserPreferenceMemoryStorageService.upsert(db, user_id, preference)

    async def update_case_memory(
        self,
        db: AsyncSession,
        case_id: UUID,
        memory_id: UUID,
        memory: CaseMemoryUpdate,
    ) -> CaseMemory | None:
        return await CaseMemoryQueryService.update(db, case_id, memory_id, memory)

    async def record_execution(
        self,
        db: AsyncSession,
        execution: AIExecution,
        workflow: OrchestrationResponse,
    ) -> None:
        """Save durable summaries only for successful executions; failures are discarded."""
        if workflow.status != "completed" or workflow.plan is None:
            return

        await self.save_case_memory(
            db,
            execution.case_id,
            CaseMemoryCreate(
                memory_type=CaseMemoryType.PLANNER_EXECUTION_SUMMARY,
                memory_key="latest_planner_execution",
                content=(
                    f"Latest completed {workflow.plan.intent.task_type.value} workflow "
                    f"executed these stages: {', '.join(workflow.trace)}."
                ),
                metadata={
                    "plan_id": str(workflow.plan.plan_id),
                    "execution_id": str(execution.id),
                    "status": workflow.status,
                },
                source_execution_id=execution.id,
            ),
        )

        if workflow.final_response and workflow.final_response.content.strip():
            await self.save_case_memory(
                db,
                execution.case_id,
                CaseMemoryCreate(
                    memory_type=CaseMemoryType.GENERATED_REPORT,
                    memory_key=f"execution:{execution.id}:report",
                    content=workflow.final_response.content.strip(),
                    metadata={"source_ids": workflow.final_response.source_ids},
                    source_execution_id=execution.id,
                ),
            )

        if workflow.analysis:
            for index, finding in enumerate(workflow.analysis.findings[:3], start=1):
                if not finding.observation.strip():
                    continue
                await self.save_case_memory(
                    db,
                    execution.case_id,
                    CaseMemoryCreate(
                        memory_type=CaseMemoryType.IMPORTANT_FINDING,
                        memory_key=f"execution:{execution.id}:finding:{index}",
                        content=finding.observation.strip(),
                        metadata={"source_ids": finding.source_ids},
                        source_execution_id=execution.id,
                    ),
                )

    @staticmethod
    async def _find_case_memory(
        db: AsyncSession,
        case_id: UUID,
        memory_type: CaseMemoryType,
        memory_key: str,
    ) -> CaseMemory | None:
        candidates = await CaseMemoryQueryService.list_for_case(
            db, case_id, memory_type=memory_type, limit=100
        )
        return next(
            (candidate for candidate in candidates if candidate.memory_key == memory_key),
            None,
        )
