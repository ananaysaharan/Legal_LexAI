"""Ranked, bounded memory retrieval for planning. It never writes memory."""

import json
import re
from typing import Protocol, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import UserPreferenceMemory
from src.api.schemas.memory import (
    PlanningMemoryContext,
    RetrievedCaseMemory,
    RetrievedUserPreference,
)
from src.api.services.memory_storage import (
    CaseMemoryQueryService,
    UserPreferenceMemoryQueryService,
)


class MemoryRanker(Protocol):
    def rank(self, query: str, memories: Sequence[object], limit: int) -> list[tuple[object, float]]: ...


class KeywordMemoryRanker:
    """Deterministic baseline replaceable with semantic or learned rankers later."""

    _token_pattern = re.compile(r"[a-z0-9_]{3,}")

    def rank(
        self, query: str, memories: Sequence[object], limit: int
    ) -> list[tuple[object, float]]:
        query_tokens = set(self._token_pattern.findall(query.lower()))
        ranked: list[tuple[object, float]] = []
        for memory in memories:
            searchable = self._searchable_text(memory)
            matches = sum(token in searchable for token in query_tokens)
            if matches:
                ranked.append((memory, matches / max(len(query_tokens), 1)))
        return sorted(ranked, key=lambda item: item[1], reverse=True)[:limit]

    @staticmethod
    def _searchable_text(memory: object) -> str:
        if hasattr(memory, "memory_type"):
            return " ".join(
                filter(
                    None,
                    [
                        memory.memory_type,
                        memory.memory_key or "",
                        memory.content,
                        json.dumps(memory.metadata_data or {}, sort_keys=True),
                    ],
                )
            ).lower()
        preference = memory
        return " ".join(
            [
                preference.preference_type,
                preference.preference_key,
                json.dumps(preference.preference_value or {}, sort_keys=True),
            ]
        ).lower()


class MemoryRetrievalService:
    """Builds a limited planning context from separately retrieved case and user memory."""

    def __init__(self, ranker: MemoryRanker | None = None) -> None:
        self._ranker = ranker or KeywordMemoryRanker()

    async def retrieve_for_planning(
        self,
        db: AsyncSession,
        case_id: UUID,
        user_id: str,
        request: str,
        case_limit: int = 5,
        preference_limit: int = 5,
    ) -> PlanningMemoryContext:
        case_candidates = await CaseMemoryQueryService.list_for_case(
            db, case_id, limit=50
        )
        preference_candidates = await UserPreferenceMemoryQueryService.list_for_user(
            db, user_id, limit=50
        )
        ranked_case = self._ranker.rank(request, case_candidates, case_limit)
        ranked_preferences = self._rank_preferences(
            request, preference_candidates, preference_limit
        )
        return PlanningMemoryContext(
            case_memories=[
                RetrievedCaseMemory(
                    id=memory.id,
                    memory_type=memory.memory_type,
                    memory_key=memory.memory_key,
                    content=memory.content,
                    metadata=memory.metadata_data or {},
                    relevance_score=score,
                )
                for memory, score in ranked_case
            ],
            user_preferences=[
                RetrievedUserPreference(
                    id=memory.id,
                    preference_type=memory.preference_type,
                    preference_key=memory.preference_key,
                    preference_value=memory.preference_value,
                    scope=memory.scope,
                    confidence=memory.confidence,
                    relevance_score=score,
                )
                for memory, score in ranked_preferences
            ],
        )

    def _rank_preferences(
        self,
        request: str,
        preferences: Sequence[UserPreferenceMemory],
        limit: int,
    ) -> list[tuple[UserPreferenceMemory, float]]:
        ranked = self._ranker.rank(request, preferences, limit)
        selected_ids = {memory.id for memory, _ in ranked}
        global_preferences = [
            preference
            for preference in preferences
            if preference.id not in selected_ids
            and preference.preference_type
            in {"preferred_report_format", "writing_style", "citation_preferences", "workflow_behavior"}
        ]
        for preference in global_preferences:
            if len(ranked) >= limit:
                break
            ranked.append((preference, 0.01))
        return ranked
