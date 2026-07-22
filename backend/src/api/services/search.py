import asyncio
from typing import List, Protocol, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api.db.models import DocumentChunk, Document, Case
from src.api.services.embeddings import generate_embeddings
from src.api.schemas.search import SearchResultChunk


class Reranker(Protocol):
    """Optional post-retrieval stage that preserves the public result contract."""

    async def rerank(
        self, query: str, candidates: Sequence[SearchResultChunk]
    ) -> Sequence[SearchResultChunk]: ...


class RetrievalService:
    """Retrieves authorized document evidence without invoking an LLM."""

    def __init__(self, rerankers: Sequence[Reranker] = ()) -> None:
        self._rerankers = rerankers

    async def retrieve(
        self,
        db: AsyncSession,
        case_id: UUID,
        user_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[SearchResultChunk]:
        """Return the top semantic candidates, optionally post-processed by rerankers."""
        # Authorize before embedding so unauthorized requests do not consume model capacity.
        case_result = await db.execute(
            select(Case.id).where(Case.id == case_id, Case.user_id == user_id)
        )
        if case_result.scalar_one_or_none() is None:
            raise ValueError("Case not found or unauthorized")

        # FastEmbed is synchronous and CPU-bound; keep it off the async event loop.
        query_embedding_list = await asyncio.to_thread(generate_embeddings, [query])
        if not query_embedding_list:
            return []

        distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding_list[0])
        stmt = (
            select(DocumentChunk, Document, distance_expr.label("distance"))
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                Document.case_id == case_id,
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(distance_expr.asc())
            .limit(top_k)
        )
        rows = (await db.execute(stmt)).all()

        results = [
            SearchResultChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_filename=document.filename,
                document_type=document.document_type,
                document_version=document.version,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                section=chunk.section,
                clause=chunk.clause,
                text_content=chunk.text_content,
                # cosine_distance = 1 - cosine_similarity
                similarity_score=float(1.0 - distance) if distance is not None else 0.0,
            )
            for chunk, document, distance in rows
        ]

        for reranker in self._rerankers:
            results = list(await reranker.rerank(query, results))
        return results


class SearchService:
    """Backward-compatible facade for the existing semantic search endpoint."""

    @staticmethod
    async def semantic_search(
        db: AsyncSession,
        case_id: UUID,
        user_id: str,
        query: str,
        top_k: int = 5
    ) -> List[SearchResultChunk]:
        return await RetrievalService().retrieve(db, case_id, user_id, query, top_k)
