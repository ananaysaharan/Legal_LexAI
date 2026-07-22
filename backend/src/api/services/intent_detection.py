"""Extensible user-task classification with no planning or retrieval side effects."""

import re
from dataclasses import dataclass
from typing import Pattern, Protocol, Sequence

from src.api.schemas.intent import Intent, IntentType


class IntentDetector(Protocol):
    def detect(self, request: str) -> Intent: ...


@dataclass(frozen=True)
class IntentRule:
    """A declarative rule that can be extended without changing detector control flow."""

    task_type: IntentType
    patterns: tuple[Pattern[str], ...]
    confidence: float
    requires_multiple_documents: bool = False


def _patterns(*values: str) -> tuple[Pattern[str], ...]:
    return tuple(re.compile(value, re.IGNORECASE) for value in values)


DEFAULT_INTENT_RULES: tuple[IntentRule, ...] = (
    IntentRule(
        task_type=IntentType.AGREEMENT_COMPARISON,
        patterns=_patterns(r"\b(compare|comparison|differences?|contrast)\b"),
        confidence=0.96,
        requires_multiple_documents=True,
    ),
    IntentRule(
        task_type=IntentType.RISK_CLAUSE_ANALYSIS,
        patterns=_patterns(r"\b(risk|risky|red flag|problematic)\b", r"\b(clause|clauses|provision|provisions|term|terms)\b"),
        confidence=0.95,
    ),
    IntentRule(
        task_type=IntentType.RESPONSE_DRAFTING,
        patterns=_patterns(r"\b(draft|write|prepare)\b", r"\b(response|reply|letter|email)\b"),
        confidence=0.94,
    ),
    IntentRule(
        task_type=IntentType.CONTRACT_REVIEW,
        patterns=_patterns(r"\b(review|analy[sz]e|assess)\b", r"\b(contract|agreement|lease|nda)\b"),
        confidence=0.93,
    ),
    IntentRule(
        task_type=IntentType.DOCUMENT_SUMMARY,
        patterns=_patterns(r"\b(summarize|summarise|summary)\b"),
        confidence=0.91,
    ),
)


class RuleBasedIntentDetector:
    """Transparent classifier intended for predictable high-level legal task requests."""

    def __init__(self, rules: Sequence[IntentRule] = DEFAULT_INTENT_RULES) -> None:
        self._rules = tuple(rules)

    def detect(self, request: str) -> Intent:
        normalized_request = " ".join(request.split())
        if not normalized_request:
            raise ValueError("request must not be blank")

        for rule in self._rules:
            matches = [pattern.search(normalized_request) for pattern in rule.patterns]
            if all(matches):
                return Intent(
                    task_type=rule.task_type,
                    confidence=rule.confidence,
                    normalized_request=normalized_request,
                    matched_signals=[match.group(0) for match in matches if match],
                    requires_multiple_documents=rule.requires_multiple_documents,
                )

        return Intent(
            task_type=IntentType.QUESTION_ANSWERING,
            confidence=0.65,
            normalized_request=normalized_request,
            matched_signals=[],
        )
