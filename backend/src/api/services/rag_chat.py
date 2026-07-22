"""Application service for the complete, memory-free RAG chat request."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.config import settings
from src.api.schemas.chat import Citation
from src.api.schemas.search import SearchResultChunk
from src.api.services.conversations import ConversationService
from src.api.services.llm import GeminiLiteLLMClient, LLMClient
from src.api.services.prompt_builder import PromptBuilder
from src.api.services.search import RetrievalService


@dataclass(frozen=True)
class RAGChatResult:
    conversation_id: UUID
    message_id: UUID
    answer: str
    sources: list[SearchResultChunk]
    citations: list[Citation]
    prompt_template_version: str


class NoGroundedContextError(ValueError):
    """Raised when no retrieved evidence can safely support an LLM answer."""


class RAGChatService:
    """Coordinates retrieval, prompt construction, generation, and persistence."""

    def __init__(
        self,
        retriever: RetrievalService | None = None,
        prompt_builder: PromptBuilder | None = None,
        llm_client: LLMClient | None = None,
        conversation_window_messages: int | None = None,
    ) -> None:
        window_messages = (
            settings.conversation_window_messages
            if conversation_window_messages is None
            else conversation_window_messages
        )
        if window_messages < 0:
            raise ValueError("conversation_window_messages must not be negative")
        self._retriever = retriever or RetrievalService()
        self._prompt_builder = prompt_builder or PromptBuilder(
            max_history_characters=settings.conversation_history_max_characters
        )
        self._llm_client = llm_client or GeminiLiteLLMClient()
        self._conversation_window_messages = window_messages

    async def chat(
        self,
        db: AsyncSession,
        case_id: UUID,
        user_id: str,
        question: str,
        top_k: int = 5,
        conversation_id: UUID | None = None,
    ) -> RAGChatResult:
        sources = await self._retriever.retrieve(db, case_id, user_id, question, top_k)
        if not sources:
            raise NoGroundedContextError("No retrieved context is available to ground an answer")

        conversation = await ConversationService.get_or_create(
            db, case_id, user_id, conversation_id
        )
        history = await ConversationService.get_recent_history(
            db, conversation.id, self._conversation_window_messages
        )
        prompt_result = self._prompt_builder.build(
            question, sources, conversation_history=history
        )
        grounded_sources, citations = self._build_citations(
            sources, prompt_result.included_chunk_ids
        )
        if not citations:
            raise NoGroundedContextError("No retrieved context is available to ground an answer")

        await ConversationService.save_message(db, conversation.id, "user", question)

        # Only the recent transcript is injected; long-term memory is intentionally absent.
        answer = await self._llm_client.complete(prompt_result.prompt)
        assistant_message = await ConversationService.save_message(
            db,
            conversation.id,
            "assistant",
            answer,
            {
                "prompt_template_version": prompt_result.template_version,
                "source_chunk_ids": list(prompt_result.included_chunk_ids),
                "citations": [citation.model_dump(mode="json") for citation in citations],
                "omitted_chunk_count": prompt_result.omitted_chunk_count,
                "model": getattr(self._llm_client, "model_name", settings.gemini_model),
            },
        )
        await db.commit()

        return RAGChatResult(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            answer=answer,
            sources=grounded_sources,
            citations=citations,
            prompt_template_version=prompt_result.template_version,
        )

    @staticmethod
    def _build_citations(
        retrieved_sources: list[SearchResultChunk],
        included_chunk_ids: tuple[str, ...],
    ) -> tuple[list[SearchResultChunk], list[Citation]]:
        """Build citations exclusively from chunks that were rendered into the prompt."""
        source_by_chunk_id = {str(source.chunk_id): source for source in retrieved_sources}
        grounded_sources: list[SearchResultChunk] = []
        citations: list[Citation] = []
        for source_number, chunk_id in enumerate(included_chunk_ids, start=1):
            source = source_by_chunk_id.get(chunk_id)
            if source is None:
                continue
            grounded_sources.append(source)
            citations.append(
                Citation(
                    source_label=f"Source {source_number}",
                    document_name=source.document_filename,
                    page_number=source.page_number,
                    chunk_id=source.chunk_id,
                )
            )
        return grounded_sources, citations
