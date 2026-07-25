"""LangGraph workflow that coordinates existing services and independent workers."""

from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.intent import Intent
from src.api.schemas.memory import PlanningMemoryContext
from src.api.schemas.orchestration import (
    FinalResponse,
    OrchestrationFailure,
    OrchestrationResponse,
)
from src.api.schemas.planner import ExecutionPlan, PlanStep, PlanStepType
from src.api.schemas.workers import (
    AnalysisWorkerInput,
    AnalysisWorkerOutput,
    EvidenceItem,
    ResearchWorkerInput,
    ResearchWorkerOutput,
    ReviewerWorkerInput,
    ReviewerWorkerOutput,
    WorkerTask,
    WriterWorkerInput,
    WriterWorkerOutput,
)
from src.api.services.intent_detection import RuleBasedIntentDetector
from src.api.services.memory_retrieval import MemoryRetrievalService
from src.api.services.planner import RuleBasedPlanner
from src.api.services.search import RetrievalService
from src.api.services.workers.analysis import AnalysisWorker
from src.api.services.workers.research import ResearchWorker
from src.api.services.workers.reviewer import ReviewerWorker
from src.api.services.workers.writer import WriterWorker


class WorkflowState(TypedDict, total=False):
    request: str
    case_id: UUID
    user_id: str
    top_k: int
    db: AsyncSession
    intent: Intent
    planning_context: PlanningMemoryContext
    plan: ExecutionPlan
    research: ResearchWorkerOutput
    analysis: AnalysisWorkerOutput
    writer: WriterWorkerOutput
    reviewer: ReviewerWorkerOutput
    final_response: FinalResponse
    error: OrchestrationFailure
    trace: list[str]


class LegalWorkflow:
    """Coordinates nodes only; worker implementations remain independently reusable."""

    def __init__(
        self,
        detector=None,
        planner=None,
        memory_retriever=None,
        retriever=None,
        research_worker=None,
        analysis_worker=None,
        writer_worker=None,
        reviewer_worker=None,
    ) -> None:
        self._detector = detector or RuleBasedIntentDetector()
        self._planner = planner or RuleBasedPlanner()
        self._memory_retriever = memory_retriever or MemoryRetrievalService()
        self._retriever = retriever or RetrievalService()
        self._research_worker = research_worker or ResearchWorker()
        self._analysis_worker = analysis_worker or AnalysisWorker()
        self._writer_worker = writer_worker or WriterWorker()
        self._reviewer_worker = reviewer_worker or ReviewerWorker()
        self._graph = self._build_graph()

    async def run(
        self,
        db: AsyncSession,
        case_id: UUID,
        user_id: str,
        request: str,
        top_k: int = 5,
    ) -> OrchestrationResponse:
        state = await self._graph.ainvoke(
            {
                "db": db,
                "case_id": case_id,
                "user_id": user_id,
                "request": request,
                "top_k": top_k,
                "trace": [],
            }
        )
        if state.get("error"):
            return OrchestrationResponse(
                status="failed",
                trace=state["trace"],
                intent=state.get("intent"),
                plan=state.get("plan"),
                research=state.get("research"),
                analysis=state.get("analysis"),
                writer=state.get("writer"),
                reviewer=state.get("reviewer"),
                error=state["error"],
            )
        return OrchestrationResponse(
            status="completed",
            trace=state["trace"],
            intent=state["intent"],
            plan=state["plan"],
            research=state["research"],
            analysis=state["analysis"],
            writer=state["writer"],
            reviewer=state["reviewer"],
            final_response=state["final_response"],
        )

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("intent", self._intent_node)
        graph.add_node("memory", self._memory_node)
        graph.add_node("planner", self._planner_node)
        graph.add_node("research", self._research_node)
        graph.add_node("analysis", self._analysis_node)
        graph.add_node("writer", self._writer_node)
        graph.add_node("reviewer", self._reviewer_node)
        graph.add_node("finalize", self._finalize_node)
        graph.add_node("failure", self._failure_node)
        graph.add_edge(START, "intent")
        for source, success in (
            ("intent", "memory"),
            ("memory", "planner"),
            ("planner", "research"),
            ("research", "analysis"),
            ("analysis", "writer"),
            ("writer", "reviewer"),
            ("reviewer", "finalize"),
        ):
            graph.add_conditional_edges(
                source,
                lambda state, next_node=success: (
                    "failure" if state.get("error") else next_node
                ),
                {"failure": "failure", success: success},
            )
        graph.add_edge("finalize", END)
        graph.add_edge("failure", END)
        return graph.compile()

    async def _intent_node(self, state: WorkflowState) -> dict:
        return self._run_node(
            state, "intent", lambda: {"intent": self._detector.detect(state["request"])}
        )

    async def _planner_node(self, state: WorkflowState) -> dict:
        return self._run_node(
            state,
            "planner",
            lambda: {
                "plan": self._planner.create_plan(
                    state["intent"], state["planning_context"]
                )
            },
        )

    async def _memory_node(self, state: WorkflowState) -> dict:
        try:
            context = await self._memory_retriever.retrieve_for_planning(
                state["db"], state["case_id"], state["user_id"], state["request"]
            )
            return self._success(state, "memory", planning_context=context)
        except Exception as exc:
            return self._failure(state, "memory", exc)

    async def _research_node(self, state: WorkflowState) -> dict:
        try:
            step = self._required_step(
                state["plan"], (PlanStepType.RETRIEVE, PlanStepType.RESEARCH)
            )
            chunks = await self._retriever.retrieve(
                state["db"],
                state["case_id"],
                state["user_id"],
                state["request"],
                state["top_k"],
            )
            if not chunks:
                raise ValueError("No retrieved evidence is available for this workflow")
            sources = [
                EvidenceItem(
                    source_id=str(chunk.chunk_id),
                    document_name=chunk.document_filename,
                    page_number=chunk.page_number,
                    content=chunk.text_content,
                )
                for chunk in chunks
            ]
            output = self._research_worker.run(
                ResearchWorkerInput(
                    task=self._worker_task(state["plan"], step), sources=sources
                )
            )
            return self._success(state, "research", research=output)
        except Exception as exc:
            return self._failure(state, "research", exc)

    async def _analysis_node(self, state: WorkflowState) -> dict:
        return self._run_node(
            state,
            "analysis",
            lambda: {
                "analysis": self._analysis_worker.run(
                    AnalysisWorkerInput(
                        task=self._worker_task(
                            state["plan"],
                            self._required_step(state["plan"], (PlanStepType.ANALYZE,)),
                        ),
                        research_findings=state["research"].findings,
                    )
                )
            },
        )

    async def _writer_node(self, state: WorkflowState) -> dict:
        return self._run_node(
            state,
            "writer",
            lambda: {
                "writer": self._writer_worker.run(
                    WriterWorkerInput(
                        task=self._worker_task(
                            state["plan"],
                            self._required_step(
                                state["plan"], (PlanStepType.GENERATE,)
                            ),
                        ),
                        findings=state["analysis"].findings,
                        title=state["plan"]
                        .intent.task_type.value.replace("_", " ")
                        .title(),
                    )
                )
            },
        )

    async def _reviewer_node(self, state: WorkflowState) -> dict:
        return self._run_node(
            state,
            "reviewer",
            lambda: {
                "reviewer": self._reviewer_worker.run(
                    ReviewerWorkerInput(
                        task=self._worker_task(
                            state["plan"],
                            self._required_step(state["plan"], (PlanStepType.REVIEW,)),
                        ),
                        draft=state["writer"].draft,
                        available_source_ids=[
                            finding.source_id for finding in state["research"].findings
                        ],
                    )
                )
            },
        )

    async def _finalize_node(self, state: WorkflowState) -> dict:
        return self._success(
            state,
            "finalize",
            final_response=FinalResponse(
                content=state["writer"].draft.content,
                source_ids=state["writer"].draft.source_ids,
                review_passed=all(check.passed for check in state["reviewer"].checks),
            ),
        )

    async def _failure_node(self, state: WorkflowState) -> dict:
        return {"trace": [*state["trace"], "failure"]}

    @staticmethod
    def _required_step(
        plan: ExecutionPlan, allowed: tuple[PlanStepType, ...]
    ) -> PlanStep:
        for step in plan.steps:
            if step.step_type in allowed:
                return step
        raise ValueError(
            f"Plan has no step for: {', '.join(item.value for item in allowed)}"
        )

    @staticmethod
    def _worker_task(plan: ExecutionPlan, step: PlanStep) -> WorkerTask:
        return WorkerTask(plan_id=plan.plan_id, intent=plan.intent, step=step)

    def _run_node(self, state: WorkflowState, node: str, operation) -> dict:
        try:
            return self._success(state, node, **operation())
        except Exception as exc:
            return self._failure(state, node, exc)

    @staticmethod
    def _success(state: WorkflowState, node: str, **updates: object) -> dict:
        return {"trace": [*state["trace"], node], **updates}

    @staticmethod
    def _failure(state: WorkflowState, node: str, exc: Exception) -> dict:
        return {
            "trace": [*state["trace"], node],
            "error": OrchestrationFailure(
                node=node, message=str(exc) or "Workflow node failed"
            ),
        }
