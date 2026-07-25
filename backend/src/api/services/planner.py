"""Intent-to-plan transformation with no retrieval, generation, or tool execution."""

import json
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Protocol, Sequence

from src.api.schemas.intent import Intent, IntentType
from src.api.schemas.memory import PlanningMemoryContext
from src.api.schemas.planner import ExecutionPlan, PlanStep, PlanStepType

PLANNER_TEMPLATE_NAME = "planner_v1.txt"
PROMPTS_DIRECTORY = Path(__file__).resolve().parent.parent / "prompts"


class Planner(Protocol):
    def create_plan(
        self, intent: Intent, planning_context: PlanningMemoryContext | None = None
    ) -> ExecutionPlan: ...


@dataclass(frozen=True)
class PlanStepBlueprint:
    step_id: str
    step_type: PlanStepType
    description: str
    inputs: tuple[str, ...]
    expected_output: str
    depends_on: tuple[str, ...] = ()


DEFAULT_PLAN_BLUEPRINTS: dict[IntentType, tuple[PlanStepBlueprint, ...]] = {
    IntentType.CONTRACT_REVIEW: (
        PlanStepBlueprint(
            "retrieve_clauses",
            PlanStepType.RETRIEVE,
            "Retrieve clauses relevant to obligations, remedies, liability, and termination.",
            ("case documents", "contract review intent"),
            "Ranked clause set",
        ),
        PlanStepBlueprint(
            "analyze_risks",
            PlanStepType.ANALYZE,
            "Analyze the retrieved clauses for legal and commercial risks.",
            ("ranked clause set",),
            "Risk findings",
            ("retrieve_clauses",),
        ),
        PlanStepBlueprint(
            "research_context",
            PlanStepType.RESEARCH,
            "Gather supporting document context for each material risk.",
            ("risk findings", "case documents"),
            "Grounded supporting context",
            ("analyze_risks",),
        ),
        PlanStepBlueprint(
            "generate_report",
            PlanStepType.GENERATE,
            "Generate a structured contract review report with sources.",
            ("risk findings", "grounded supporting context"),
            "Draft review report",
            ("analyze_risks", "research_context"),
        ),
        PlanStepBlueprint(
            "review_output",
            PlanStepType.REVIEW,
            "Review the report for completeness, source coverage, and task alignment.",
            ("draft review report",),
            "Reviewed final report",
            ("generate_report",),
        ),
    ),
    IntentType.DOCUMENT_SUMMARY: (
        PlanStepBlueprint(
            "retrieve_content",
            PlanStepType.RETRIEVE,
            "Retrieve the document sections needed for a complete summary.",
            ("case documents", "summary intent"),
            "Relevant document sections",
        ),
        PlanStepBlueprint(
            "analyze_content",
            PlanStepType.ANALYZE,
            "Analyze the retrieved sections for key facts, issues, and chronology.",
            ("relevant document sections",),
            "Summary findings",
            ("retrieve_content",),
        ),
        PlanStepBlueprint(
            "generate_summary",
            PlanStepType.GENERATE,
            "Generate a concise, source-grounded summary.",
            ("summary findings",),
            "Draft summary",
            ("analyze_content",),
        ),
        PlanStepBlueprint(
            "review_output",
            PlanStepType.REVIEW,
            "Review the summary for coverage and source support.",
            ("draft summary",),
            "Reviewed final summary",
            ("generate_summary",),
        ),
    ),
    IntentType.AGREEMENT_COMPARISON: (
        PlanStepBlueprint(
            "retrieve_agreements",
            PlanStepType.RETRIEVE,
            "Retrieve relevant clauses from each agreement.",
            ("multiple case documents", "comparison intent"),
            "Aligned clause sets",
        ),
        PlanStepBlueprint(
            "analyze_differences",
            PlanStepType.ANALYZE,
            "Analyze material similarities, differences, and conflicts.",
            ("aligned clause sets",),
            "Comparison findings",
            ("retrieve_agreements",),
        ),
        PlanStepBlueprint(
            "generate_comparison",
            PlanStepType.GENERATE,
            "Generate a source-grounded comparison report.",
            ("comparison findings",),
            "Draft comparison report",
            ("analyze_differences",),
        ),
        PlanStepBlueprint(
            "review_output",
            PlanStepType.REVIEW,
            "Review the comparison for document coverage and accuracy.",
            ("draft comparison report",),
            "Reviewed final comparison",
            ("generate_comparison",),
        ),
    ),
    IntentType.RESPONSE_DRAFTING: (
        PlanStepBlueprint(
            "retrieve_context",
            PlanStepType.RETRIEVE,
            "Retrieve facts, positions, and source language relevant to the requested response.",
            ("case documents", "drafting intent"),
            "Grounded response context",
        ),
        PlanStepBlueprint(
            "analyze_context",
            PlanStepType.ANALYZE,
            "Analyze the retrieved context for the requested response position and supporting facts.",
            ("grounded response context",),
            "Response findings",
            ("retrieve_context",),
        ),
        PlanStepBlueprint(
            "generate_draft",
            PlanStepType.GENERATE,
            "Generate a draft response constrained to the retrieved context.",
            ("response findings",),
            "Draft response",
            ("analyze_context",),
        ),
        PlanStepBlueprint(
            "review_output",
            PlanStepType.REVIEW,
            "Review the draft for source support, completeness, and tone.",
            ("draft response",),
            "Reviewed final draft",
            ("generate_draft",),
        ),
    ),
    IntentType.RISK_CLAUSE_ANALYSIS: (
        PlanStepBlueprint(
            "retrieve_risk_clauses",
            PlanStepType.RETRIEVE,
            "Retrieve clauses related to risk allocation, liability, remedies, and termination.",
            ("case documents", "risk analysis intent"),
            "Candidate risk clauses",
        ),
        PlanStepBlueprint(
            "analyze_risks",
            PlanStepType.ANALYZE,
            "Analyze candidate clauses for risk exposure and missing protections.",
            ("candidate risk clauses",),
            "Risk findings",
            ("retrieve_risk_clauses",),
        ),
        PlanStepBlueprint(
            "generate_report",
            PlanStepType.GENERATE,
            "Generate a source-grounded risk report.",
            ("risk findings",),
            "Draft risk report",
            ("analyze_risks",),
        ),
        PlanStepBlueprint(
            "review_output",
            PlanStepType.REVIEW,
            "Review the report for source coverage and prioritization.",
            ("draft risk report",),
            "Reviewed final risk report",
            ("generate_report",),
        ),
    ),
}

DEFAULT_QUESTION_PLAN: tuple[PlanStepBlueprint, ...] = (
    PlanStepBlueprint(
        "retrieve_context",
        PlanStepType.RETRIEVE,
        "Retrieve context relevant to the user's question.",
        ("case documents", "user request"),
        "Ranked source context",
    ),
    PlanStepBlueprint(
        "analyze_context",
        PlanStepType.ANALYZE,
        "Analyze the retrieved context for the user's question.",
        ("ranked source context",),
        "Answer findings",
        ("retrieve_context",),
    ),
    PlanStepBlueprint(
        "generate_answer",
        PlanStepType.GENERATE,
        "Generate a source-grounded answer.",
        ("answer findings",),
        "Draft answer",
        ("analyze_context",),
    ),
    PlanStepBlueprint(
        "review_output",
        PlanStepType.REVIEW,
        "Review the answer for source support and completeness.",
        ("draft answer",),
        "Reviewed final answer",
        ("generate_answer",),
    ),
)


class PlannerPromptBuilder:
    """Loads the versioned future-LLM planning contract from a prompt file."""

    def __init__(self, template_name: str = PLANNER_TEMPLATE_NAME) -> None:
        if Path(template_name).name != template_name:
            raise ValueError("template_name must be a filename")
        self._template_name = template_name
        self._template = Template(
            (PROMPTS_DIRECTORY / template_name).read_text(encoding="utf-8")
        )

    @property
    def version(self) -> str:
        return Path(self._template_name).stem

    def build(
        self, intent: Intent, planning_context: PlanningMemoryContext | None = None
    ) -> str:
        return self._template.substitute(
            intent_json=json.dumps(
                intent.model_dump(mode="json"), indent=2, sort_keys=True
            ),
            planning_context_json=json.dumps(
                (planning_context or PlanningMemoryContext()).model_dump(mode="json"),
                indent=2,
                sort_keys=True,
            ),
        )


class RuleBasedPlanner:
    """Produces declarative plan blueprints; it intentionally cannot execute a plan."""

    def __init__(self, prompt_builder: PlannerPromptBuilder | None = None) -> None:
        self._prompt_builder = prompt_builder or PlannerPromptBuilder()

    def create_plan(
        self, intent: Intent, planning_context: PlanningMemoryContext | None = None
    ) -> ExecutionPlan:
        # Render and validate the external prompt contract for future LLM planners.
        context = planning_context or PlanningMemoryContext()
        self._prompt_builder.build(intent, context)
        blueprints = DEFAULT_PLAN_BLUEPRINTS.get(
            intent.task_type, DEFAULT_QUESTION_PLAN
        )
        return ExecutionPlan(
            prompt_template_version=self._prompt_builder.version,
            intent=intent,
            planning_context=context,
            steps=[
                PlanStep(
                    step_id=blueprint.step_id,
                    step_type=blueprint.step_type,
                    description=blueprint.description,
                    inputs=list(blueprint.inputs),
                    expected_output=blueprint.expected_output,
                    depends_on=list(blueprint.depends_on),
                )
                for blueprint in blueprints
            ],
        )
