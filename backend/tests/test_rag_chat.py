import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api.schemas.search import SearchResultChunk
from src.api.services.prompt_builder import ConversationTurn
from src.api.services.rag_chat import RAGChatService


class FakeRetriever:
    async def retrieve(self, db, case_id, user_id, query, top_k):
        return [
            SearchResultChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                document_filename="lease.pdf",
                page_number=2,
                chunk_index=0,
                text_content="The tenant must provide 60 days notice.",
                similarity_score=0.95,
            )
        ]


class FakeLLM:
    async def complete(self, prompt: str) -> str:
        self.prompt = prompt
        return "The lease requires 60 days notice. [Source 1]"


class RAGChatServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_orchestrates_retrieval_prompt_generation_and_persistence(self) -> None:
        llm = FakeLLM()
        db = SimpleNamespace(commit=AsyncMock())
        conversation = SimpleNamespace(id=uuid4())
        assistant_message = SimpleNamespace(id=uuid4())

        with (
            patch(
                "src.api.services.rag_chat.ConversationService.get_or_create",
                new=AsyncMock(return_value=conversation),
            ),
            patch(
                "src.api.services.rag_chat.ConversationService.get_recent_history",
                new=AsyncMock(
                    return_value=[
                        ConversationTurn(role="user", content="What does the lease say?")
                    ]
                ),
            ) as get_recent_history,
            patch(
                "src.api.services.rag_chat.ConversationService.save_message",
                new=AsyncMock(side_effect=[None, assistant_message]),
            ) as save_message,
        ):
            result = await RAGChatService(
                retriever=FakeRetriever(), llm_client=llm
            ).chat(
                db=db,
                case_id=uuid4(),
                user_id="user-1",
                question="How much notice is required?",
            )

        self.assertEqual(result.answer, "The lease requires 60 days notice. [Source 1]")
        self.assertEqual(result.conversation_id, conversation.id)
        self.assertEqual(result.message_id, assistant_message.id)
        self.assertIn("How much notice is required?", llm.prompt)
        self.assertIn("[user] What does the lease say?", llm.prompt)
        self.assertIn("[Source 1", llm.prompt)
        self.assertEqual(len(result.citations), 1)
        self.assertEqual(result.citations[0].source_label, "Source 1")
        self.assertEqual(result.citations[0].document_name, "lease.pdf")
        self.assertEqual(result.citations[0].page_number, 2)
        self.assertEqual(result.citations[0].chunk_id, result.sources[0].chunk_id)
        self.assertEqual(save_message.await_count, 2)
        get_recent_history.assert_awaited_once_with(db, conversation.id, 8)
        db.commit.assert_awaited_once()

    async def test_rejects_generation_without_retrieved_context(self) -> None:
        class EmptyRetriever:
            async def retrieve(self, *args, **kwargs):
                return []

        with self.assertRaisesRegex(ValueError, "No retrieved context"):
            await RAGChatService(retriever=EmptyRetriever(), llm_client=FakeLLM()).chat(
                db=SimpleNamespace(commit=AsyncMock()),
                case_id=uuid4(),
                user_id="user-1",
                question="What is the notice period?",
            )


if __name__ == "__main__":
    unittest.main()
