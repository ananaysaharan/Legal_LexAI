import unittest
from uuid import uuid4

from src.api.schemas.search import SearchResultChunk
from src.api.services.prompt_builder import ConversationTurn, PromptBuilder


def make_chunk(text: str) -> SearchResultChunk:
    return SearchResultChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        document_filename="agreement.pdf",
        document_type="agreement",
        document_version="v1",
        page_number=4,
        chunk_index=2,
        section="Termination",
        clause="12.1",
        text_content=text,
        similarity_score=0.93,
    )


class PromptBuilderTests(unittest.TestCase):
    def test_build_includes_question_context_metadata_and_history(self) -> None:
        result = PromptBuilder().build(
            "When may the agreement be terminated?",
            [make_chunk("Either party may terminate with 30 days notice.")],
            [ConversationTurn(role="user", content="Review the termination terms.")],
        )

        self.assertEqual(result.template_version, "legal_context_v2")
        self.assertIn("only from the retrieved context", result.prompt)
        self.assertIn("[Source 1", result.prompt)
        self.assertIn("document=agreement.pdf", result.prompt)
        self.assertIn("[user] Review the termination terms.", result.prompt)
        self.assertIn("When may the agreement be terminated?", result.prompt)

    def test_build_respects_context_budget(self) -> None:
        result = PromptBuilder(max_context_characters=500).build(
            "Question", [make_chunk("x" * 1_000), make_chunk("second chunk")]
        )

        self.assertEqual(len(result.included_chunk_ids), 1)
        self.assertEqual(result.omitted_chunk_count, 1)
        self.assertIn("[Content truncated]", result.prompt)

    def test_build_uses_only_the_most_recent_history_within_its_budget(self) -> None:
        result = PromptBuilder(max_history_characters=45).build(
            "Question",
            [make_chunk("Evidence")],
            [
                ConversationTurn(role="user", content="older turn that does not fit"),
                ConversationTurn(role="assistant", content="recent response"),
            ],
        )

        self.assertNotIn("older turn", result.prompt)
        self.assertIn("[assistant] recent response", result.prompt)


if __name__ == "__main__":
    unittest.main()
