"""Persistence for case-scoped conversations; this service does not provide memory."""

from typing import Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import Case, Conversation, ConversationMessage
from src.api.services.prompt_builder import ConversationTurn


class ConversationService:
    @staticmethod
    async def get_or_create(
        db: AsyncSession,
        case_id: UUID,
        user_id: str,
        conversation_id: UUID | None,
    ) -> Conversation:
        if conversation_id is None:
            conversation = Conversation(case_id=case_id)
            db.add(conversation)
            await db.flush()
            return conversation

        result = await db.execute(
            select(Conversation)
            .join(Case, Conversation.case_id == Case.id)
            .where(
                Conversation.id == conversation_id,
                Conversation.case_id == case_id,
                Case.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise ValueError("Conversation not found or unauthorized")
        return conversation

    @staticmethod
    async def save_message(
        db: AsyncSession,
        conversation_id: UUID,
        role: str,
        content: str,
        message_metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=message_metadata or {},
        )
        db.add(message)
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=datetime.utcnow())
        )
        await db.flush()
        return message

    @staticmethod
    async def get_recent_history(
        db: AsyncSession,
        conversation_id: UUID,
        limit: int,
    ) -> list[ConversationTurn]:
        """Return the latest transcript turns in chronological order, without summary memory."""
        if limit < 0:
            raise ValueError("limit must not be negative")
        if limit == 0:
            return []

        result = await db.execute(
            select(ConversationMessage.role, ConversationMessage.content)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc())
            .limit(limit)
        )
        newest_first = [
            ConversationTurn(role=row.role, content=row.content)
            for row in result.all()
        ]
        return list(reversed(newest_first))
