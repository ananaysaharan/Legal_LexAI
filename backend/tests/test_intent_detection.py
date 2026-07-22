import unittest

from src.api.schemas.intent import IntentType
from src.api.services.intent_detection import IntentRule, RuleBasedIntentDetector, _patterns


class IntentDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = RuleBasedIntentDetector()

    def test_detects_high_level_legal_tasks(self) -> None:
        cases = {
            "Review this contract for material issues.": IntentType.CONTRACT_REVIEW,
            "Summarize this filing.": IntentType.DOCUMENT_SUMMARY,
            "Compare these two agreements.": IntentType.AGREEMENT_COMPARISON,
            "Draft a response to the demand letter.": IntentType.RESPONSE_DRAFTING,
            "Find risky clauses in this agreement.": IntentType.RISK_CLAUSE_ANALYSIS,
        }
        for request, task_type in cases.items():
            with self.subTest(request=request):
                self.assertEqual(self.detector.detect(request).task_type, task_type)

    def test_comparison_requires_multiple_documents(self) -> None:
        intent = self.detector.detect("Compare the agreements")
        self.assertTrue(intent.requires_retrieval)
        self.assertTrue(intent.requires_multiple_documents)
        self.assertEqual(intent.matched_signals, ["Compare"])

    def test_falls_back_to_question_answering(self) -> None:
        intent = self.detector.detect("When does the lease terminate?")
        self.assertEqual(intent.task_type, IntentType.QUESTION_ANSWERING)
        self.assertEqual(intent.confidence, 0.65)

    def test_accepts_extended_rule_sets(self) -> None:
        custom_rule = IntentRule(
            task_type=IntentType.UNKNOWN,
            patterns=_patterns(r"\btriage\b"),
            confidence=0.9,
        )
        intent = RuleBasedIntentDetector((custom_rule,)).detect("Triage this filing")
        self.assertEqual(intent.task_type, IntentType.UNKNOWN)
        self.assertEqual(intent.matched_signals, ["Triage"])


if __name__ == "__main__":
    unittest.main()
