import unittest

from src.api.schemas.intent import Intent, IntentType
from src.api.schemas.planner import PlanStepType
from src.api.services.planner import PlannerPromptBuilder, RuleBasedPlanner


def make_intent(task_type: IntentType) -> Intent:
    return Intent(
        task_type=task_type,
        confidence=0.95,
        normalized_request="Review this contract.",
        matched_signals=["Review"],
        requires_multiple_documents=task_type == IntentType.AGREEMENT_COMPARISON,
    )


class PlannerTests(unittest.TestCase):
    def test_contract_review_plan_is_ordered_and_non_executing(self) -> None:
        plan = RuleBasedPlanner().create_plan(make_intent(IntentType.CONTRACT_REVIEW))

        self.assertEqual(plan.status, "planned")
        self.assertEqual(plan.prompt_template_version, "planner_v1")
        self.assertEqual([step.step_id for step in plan.steps], [
            "retrieve_clauses",
            "analyze_risks",
            "research_context",
            "generate_report",
            "review_output",
        ])
        self.assertEqual(plan.steps[0].step_type, PlanStepType.RETRIEVE)
        self.assertEqual(plan.steps[-1].depends_on, ["generate_report"])

    def test_comparison_plan_declares_multi_document_work(self) -> None:
        plan = RuleBasedPlanner().create_plan(make_intent(IntentType.AGREEMENT_COMPARISON))
        self.assertTrue(plan.intent.requires_multiple_documents)
        self.assertEqual(plan.steps[0].inputs[0], "multiple case documents")

    def test_prompt_is_rendered_from_external_template(self) -> None:
        prompt = PlannerPromptBuilder().build(make_intent(IntentType.DOCUMENT_SUMMARY))
        self.assertIn("legal workflow planner", prompt)
        self.assertIn('"task_type": "document_summary"', prompt)


if __name__ == "__main__":
    unittest.main()
