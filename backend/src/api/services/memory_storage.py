"""Memory persistence services. Queries stay separate from writes and prompt injection."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.models import CaseMemory, UserPreferenceMemory
from src.api.schemas.memory import (
    CaseMemoryCreate,
    CaseMemoryType,
    CaseMemoryUpdate,
    PreferenceUpdateStrategy,
    UserPreferenceMemoryUpsert,
    UserPreferenceType,
)


class CaseMemoryStorageService:
    """Writes curated case facts with source provenance; it never retrieves memories."""

    @staticmethod
    async def store(
        db: AsyncSession, case_id: UUID, memory: CaseMemoryCreate
    ) -> CaseMemory:
        record = CaseMemory(
            case_id=case_id,
            memory_type=memory.memory_type.value,
            memory_key=memory.memory_key,
            content=memory.content,
            metadata_data=memory.metadata,
            source_execution_id=memory.source_execution_id,
            source_document_id=memory.source_document_id,
            source_conversation_id=memory.source_conversation_id,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record


class CaseMemoryQueryService:
    """Reads and updates case memory only; it does not write new memories or rank them."""

    @staticmethod
    async def list_for_case(
        db: AsyncSession,
        case_id: UUID,
        memory_type: CaseMemoryType | None = None,
        limit: int = 50,
    ) -> list[CaseMemory]:
        statement = select(CaseMemory).where(CaseMemory.case_id == case_id)
        if memory_type is not None:
            statement = statement.where(CaseMemory.memory_type == memory_type.value)
        statement = statement.order_by(CaseMemory.updated_at.desc()).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        case_id: UUID,
        memory_id: UUID,
        memory: CaseMemoryUpdate,
    ) -> CaseMemory | None:
        result = await db.execute(
            select(CaseMemory).where(
                CaseMemory.id == memory_id,
                CaseMemory.case_id == case_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None

        for field_name, model_name in (
            ("memory_key", "memory_key"),
            ("content", "content"),
            ("metadata", "metadata_data"),
            ("source_execution_id", "source_execution_id"),
            ("source_document_id", "source_document_id"),
            ("source_conversation_id", "source_conversation_id"),
        ):
            if field_name in memory.model_fields_set:
                setattr(record, model_name, getattr(memory, field_name))

        await db.commit()
        await db.refresh(record)
        return record


class UserPreferenceMemoryStorageService:
    """Writes cross-case preferences; it never accesses cases or conversations."""

    @staticmethod
    async def upsert(
        db: AsyncSession, user_id: str, preference: UserPreferenceMemoryUpsert
    ) -> UserPreferenceMemory:
        result = await db.execute(
            select(UserPreferenceMemory).where(
                UserPreferenceMemory.user_id == user_id,
                UserPreferenceMemory.preference_key == preference.preference_key,
                UserPreferenceMemory.scope == preference.scope,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            record = UserPreferenceMemory(
                user_id=user_id,
                preference_type=preference.preference_type.value,
                preference_key=preference.preference_key,
                preference_value=preference.preference_value,
                scope=preference.scope,
                metadata_data=preference.metadata,
                confidence=preference.confidence,
                usage_count=1 if preference.update_strategy == PreferenceUpdateStrategy.INCREMENT_USAGE else 0,
                last_used_at=datetime.now(UTC).replace(tzinfo=None),
                is_active=True,
            )
            db.add(record)
        else:
            record.preference_type = preference.preference_type.value
            record.is_active = True
            record.last_used_at = datetime.now(UTC).replace(tzinfo=None)

            if preference.update_strategy == PreferenceUpdateStrategy.REPLACE:
                record.preference_value = preference.preference_value
                record.metadata_data = preference.metadata
                record.confidence = preference.confidence
            elif preference.update_strategy == PreferenceUpdateStrategy.MERGE:
                record.preference_value = {
                    **(record.preference_value or {}),
                    **preference.preference_value,
                }
                record.metadata_data = {
                    **(record.metadata_data or {}),
                    **preference.metadata,
                }
                record.confidence = preference.confidence
            else:
                record.usage_count += 1

        await db.commit()
        await db.refresh(record)
        return record


class UserPreferenceMemoryQueryService:
    """Reads active user preferences only; it never changes preference state."""

    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        user_id: str,
        preference_type: UserPreferenceType | None = None,
        scope: str | None = None,
        limit: int = 50,
    ) -> list[UserPreferenceMemory]:
        statement = select(UserPreferenceMemory).where(
            UserPreferenceMemory.user_id == user_id,
            UserPreferenceMemory.is_active.is_(True),
        )
        if preference_type is not None:
            statement = statement.where(
                UserPreferenceMemory.preference_type == preference_type.value
            )
        if scope is not None:
            statement = statement.where(UserPreferenceMemory.scope == scope)
        statement = statement.order_by(
            UserPreferenceMemory.last_used_at.desc(),
            UserPreferenceMemory.updated_at.desc(),
        ).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())
