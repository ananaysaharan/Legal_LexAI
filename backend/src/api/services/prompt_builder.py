"""Builds versioned, document-grounded prompts without calling an LLM."""

from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Sequence

from src.api.schemas.search import SearchResultChunk


PROMPTS_DIRECTORY = Path(__file__).resolve().parent.parent / "prompts"
DEFAULT_TEMPLATE_NAME = "legal_context_v2.txt"


@dataclass(frozen=True)
class ConversationTurn:
    """A prior turn supplied by a future conversation-memory service."""

    role: str
    content: str


@dataclass(frozen=True)
class PromptBuildResult:
    """A rendered prompt and the exact source labels available to a future LLM client."""

    prompt: str
    template_version: str
    included_chunk_ids: tuple[str, ...]
    omitted_chunk_count: int


class PromptBuilder:
    """Formats retrieval evidence into a bounded, versioned LLM prompt."""

    def __init__(
        self,
        template_name: str = DEFAULT_TEMPLATE_NAME,
        max_context_characters: int = 24_000,
        max_history_characters: int = 6_000,
    ) -> None:
        if max_context_characters < 1:
            raise ValueError("max_context_characters must be positive")
        if max_history_characters < 0:
            raise ValueError("max_history_characters must not be negative")
        if Path(template_name).name != template_name:
            raise ValueError("template_name must be a filename")

        self._template_name = template_name
        self._max_context_characters = max_context_characters
        self._max_history_characters = max_history_characters
        self._template = self._load_template(template_name)

    def build(
        self,
        user_question: str,
        retrieved_chunks: Sequence[SearchResultChunk],
        conversation_history: Sequence[ConversationTurn] = (),
    ) -> PromptBuildResult:
        """Render a prompt from a question, ordered retrieval results, and optional history."""
        question = user_question.strip()
        if not question:
            raise ValueError("user_question must not be blank")

        retrieved_context, chunk_ids, omitted_chunk_count = self._format_context(
            retrieved_chunks
        )
        prompt = self._template.substitute(
            conversation_history=self._format_history(
                conversation_history, self._max_history_characters
            ),
            retrieved_context=retrieved_context,
            user_question=question,
        )
        return PromptBuildResult(
            prompt=prompt,
            template_version=Path(self._template_name).stem,
            included_chunk_ids=tuple(chunk_ids),
            omitted_chunk_count=omitted_chunk_count,
        )

    def _format_context(
        self, chunks: Sequence[SearchResultChunk]
    ) -> tuple[str, list[str], int]:
        if not chunks:
            return "No retrieved context is available.", [], 0

        remaining = self._max_context_characters
        entries: list[str] = []
        included_chunk_ids: list[str] = []
        omitted_chunk_count = 0
        for source_number, chunk in enumerate(chunks, start=1):
            entry = self._format_chunk(source_number, chunk)
            separator_size = 2 if entries else 0
            if len(entry) > remaining:
                # Keep as much source metadata/evidence as the configured budget allows.
                truncation_marker = "\n[Content truncated]"
                available_entry_size = max(0, remaining - separator_size)
                prefix_size = max(0, available_entry_size - len(truncation_marker))
                entry = entry[:prefix_size].rstrip() + truncation_marker
                entries.append(entry)
                included_chunk_ids.append(str(chunk.chunk_id))
                omitted_chunk_count = len(chunks) - source_number
                break
            entries.append(entry)
            included_chunk_ids.append(str(chunk.chunk_id))
            remaining -= len(entry) + separator_size

        return "\n\n".join(entries), included_chunk_ids, omitted_chunk_count

    @staticmethod
    def _format_chunk(source_number: int, chunk: SearchResultChunk) -> str:
        metadata = [
            f"document={chunk.document_filename}",
            f"document_id={chunk.document_id}",
            f"chunk_id={chunk.chunk_id}",
            f"page={chunk.page_number}",
            f"chunk_index={chunk.chunk_index}",
        ]
        if chunk.document_type:
            metadata.append(f"document_type={chunk.document_type}")
        if chunk.document_version:
            metadata.append(f"document_version={chunk.document_version}")
        if chunk.section:
            metadata.append(f"section={chunk.section}")
        if chunk.clause:
            metadata.append(f"clause={chunk.clause}")

        return (
            f"[Source {source_number} | {' | '.join(metadata)}]\n"
            f"{chunk.text_content.strip()}\n"
            f"[/Source {source_number}]"
        )

    @staticmethod
    def _format_history(
        history: Sequence[ConversationTurn], max_characters: int
    ) -> str:
        if not history or max_characters == 0:
            return "No conversation history is available."

        formatted_turns = [
            f"[{turn.role.strip().lower() or 'unknown'}] {turn.content.strip()}"
            for turn in history
            if turn.content.strip()
        ]
        selected_newest_first: list[str] = []
        remaining = max_characters
        for turn in reversed(formatted_turns):
            separator_size = 1 if selected_newest_first else 0
            if len(turn) + separator_size <= remaining:
                selected_newest_first.append(turn)
                remaining -= len(turn) + separator_size
            elif not selected_newest_first and remaining:
                # A single oversized latest turn is clipped rather than exceeding the budget.
                selected_newest_first.append(turn[:remaining].rstrip())
                break
            else:
                break

        if not selected_newest_first:
            return "No conversation history is available."
        return "\n".join(reversed(selected_newest_first))

    @staticmethod
    def _load_template(template_name: str) -> Template:
        template_path = PROMPTS_DIRECTORY / template_name
        try:
            return Template(template_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError(f"Prompt template not found: {template_name}") from exc
