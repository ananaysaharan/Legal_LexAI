from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.db.models import DocumentChunk, Document, Case
from src.api.services.embeddings import generate_embeddings
from src.api.schemas.search import SearchResultChunk

class SearchService:
    @staticmethod
    async def semantic_search(
        db: AsyncSession, 
        case_id: UUID, 
        user_id: str, 
        query: str, 
        top_k: int = 5
    ) -> List[SearchResultChunk]:
        # 1. Authorize: Ensure the case belongs to the user
        case_result = await db.execute(
            select(Case).filter(Case.id == case_id, Case.user_id == user_id)
        )
        case = case_result.scalars().first()
        if not case:
            raise ValueError("Case not found or unauthorized")

        # 2. Generate embedding for the query string
        # generate_embeddings returns a list of lists, we take the first (and only) one
        query_embedding_list = generate_embeddings([query])
        if not query_embedding_list:
            return []
        query_vector = query_embedding_list[0]

        # 3. Construct the vector similarity search query
        # pgvector's cosine_distance returns (1 - cosine_similarity).
        # We order by this distance (ascending) to get the closest matches.
        distance_expr = DocumentChunk.embedding.cosine_distance(query_vector)
        
        stmt = (
            select(DocumentChunk, distance_expr.label("distance"))
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(Document.case_id == case_id)
            .order_by(distance_expr)
            .limit(top_k)
        )

        result = await db.execute(stmt)
        rows = result.all()

        # 4. Map DB rows to response schema
        search_results = []
        for row in rows:
            chunk = row.DocumentChunk
            distance = row.distance
            
            # Convert distance to similarity score (higher is better)
            # Cosine distance = 1 - cosine similarity
            similarity = 1.0 - distance if distance is not None else 0.0
            
            search_results.append(
                SearchResultChunk(
                    document_id=chunk.document_id,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    clause=chunk.clause,
                    text_content=chunk.text_content,
                    similarity_score=similarity
                )
            )

        return search_results
