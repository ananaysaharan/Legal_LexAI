from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.db.models import Case, Document
from src.api.schemas.cases import CaseCreate

class CaseService:
    
    @staticmethod
    async def get_user_cases(db: AsyncSession, user_id: str) -> List[Case]:
        result = await db.execute(select(Case).where(Case.user_id == user_id))
        return result.scalars().all()

    @staticmethod
    async def get_case_by_id(db: AsyncSession, case_id: UUID, user_id: str) -> Case:
        result = await db.execute(
            select(Case).where(Case.id == case_id, Case.user_id == user_id)
        )
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found or unauthorized")
        return case

    @staticmethod
    async def create_case(db: AsyncSession, case_data: CaseCreate, user_id: str) -> Case:
        db_case = Case(**case_data.model_dump(), user_id=user_id)
        db.add(db_case)
        await db.commit()
        await db.refresh(db_case)
        return db_case

    @staticmethod
    async def delete_case(db: AsyncSession, case_id: UUID, user_id: str) -> None:
        case = await CaseService.get_case_by_id(db, case_id, user_id)
        # Note: documents are cascaded in DB, but we should also delete from Supabase storage
        # Ideally, we trigger a background task here to clean up Supabase storage
        await db.delete(case)
        await db.commit()

class DocumentService:

    @staticmethod
    async def get_case_documents(db: AsyncSession, case_id: UUID, user_id: str) -> List[Document]:
        # Ensure user owns the case first
        await CaseService.get_case_by_id(db, case_id, user_id)
        
        result = await db.execute(select(Document).where(Document.case_id == case_id))
        return result.scalars().all()

    @staticmethod
    async def create_document_record(
        db: AsyncSession, 
        case_id: UUID, 
        filename: str, 
        storage_path: str, 
        content_type: str, 
        size_bytes: int,
        document_type: str = None,
        version: str = None
    ) -> Document:
        db_doc = Document(
            case_id=case_id,
            filename=filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
            document_type=document_type,
            version=version
        )
        db.add(db_doc)
        await db.commit()
        await db.refresh(db_doc)
        return db_doc

    @staticmethod
    async def get_document_by_id(db: AsyncSession, document_id: UUID, case_id: UUID, user_id: str) -> Document:
        # Validate ownership
        await CaseService.get_case_by_id(db, case_id, user_id)
        
        result = await db.execute(
            select(Document).where(Document.id == document_id, Document.case_id == case_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return doc
        
    @staticmethod
    async def delete_document_record(db: AsyncSession, doc: Document) -> None:
        await db.delete(doc)
        await db.commit()

    @staticmethod
    async def save_document_pages(db: AsyncSession, document_id: UUID, pages_data: List[dict]) -> None:
        from src.api.db.models import DocumentPage
        for page in pages_data:
            db_page = DocumentPage(
                document_id=document_id,
                page_number=page["page_number"],
                text_content=page["text_content"]
            )
            db.add(db_page)
        await db.commit()

    @staticmethod
    async def save_document_chunks(db: AsyncSession, document_id: UUID, chunks_data: List[dict]) -> None:
        from src.api.db.models import DocumentChunk
        for chunk in chunks_data:
            db_chunk = DocumentChunk(
                document_id=document_id,
                page_number=chunk["page_number"],
                chunk_index=chunk["chunk_index"],
                section=chunk.get("section"),
                clause=chunk.get("clause"),
                text_content=chunk["text_content"],
                embedding=chunk.get("embedding")
            )
            db.add(db_chunk)
        await db.commit()
