import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.services.parsing import extract_text_from_pdf
from src.api.services.chunking import chunk_text
from src.api.services.embeddings import generate_embeddings
from src.api.services.cases import DocumentService

logger = logging.getLogger(__name__)

class DocumentPipelineService:
    @staticmethod
    async def process_document(db: AsyncSession, document_id: UUID, file_bytes: bytes) -> None:
        """
        Orchestrates the semantic processing pipeline for an uploaded document.
        Handles failures gracefully so the main upload route doesn't crash if semantics fail.
        """
        try:
            # Stage 1: Parsing
            logger.info(f"Starting parsing for document {document_id}")
            pages_data = extract_text_from_pdf(file_bytes)
            await DocumentService.save_document_pages(db, document_id, pages_data)
            
            # Stage 2: Chunking
            logger.info(f"Starting chunking for document {document_id}")
            chunks_data = []
            for page in pages_data:
                page_chunks = chunk_text(page["text_content"])
                for idx, chunk_dict in enumerate(page_chunks):
                    chunks_data.append({
                        "page_number": page["page_number"],
                        "chunk_index": idx,
                        "section": chunk_dict.get("section"),
                        "clause": chunk_dict.get("clause"),
                        "text_content": chunk_dict.get("text_content")
                    })
            
            # Stage 3: Embeddings
            logger.info(f"Starting embedding generation for document {document_id} ({len(chunks_data)} chunks)")
            if chunks_data:
                texts_to_embed = [chunk["text_content"] for chunk in chunks_data]
                embeddings = generate_embeddings(texts_to_embed)
                
                for chunk, emb in zip(chunks_data, embeddings):
                    chunk["embedding"] = emb
                    
            # Stage 4: Storage
            logger.info(f"Saving chunks to database for document {document_id}")
            await DocumentService.save_document_chunks(db, document_id, chunks_data)
            
            logger.info(f"Successfully processed document {document_id}")
            
        except Exception as e:
            # Graceful degradation: If parsing, chunking, or embedding fails, 
            # we log the error but do NOT crash. The physical file and metadata 
            # are already saved.
            logger.error(f"Pipeline failed for document {document_id}: {str(e)}", exc_info=True)
            # In a future iteration, update a processing_status column on the Document model here
