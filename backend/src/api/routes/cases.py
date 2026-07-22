import uuid
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db.database import get_db
from src.api.core.security import get_current_user
from src.api.schemas.cases import CaseCreate, CaseResponse, DocumentResponse
from src.api.schemas.chat import ChatRequest, ChatResponse
from src.api.schemas.search import SearchRequest, SearchResponse
from src.api.services.cases import CaseService, DocumentService
from src.api.services.llm import LLMProviderError
from src.api.services.rag_chat import NoGroundedContextError, RAGChatService
from src.api.services.storage import storage_service

router = APIRouter()

# Dependency aliases to make route signatures cleaner
CurrentUser = Depends(get_current_user)
DbSession = Depends(get_db)

# --- CASES ---

@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(case_data: CaseCreate, db: AsyncSession = DbSession, current_user: dict = CurrentUser):
    return await CaseService.create_case(db, case_data, current_user["sub"])

@router.get("/", response_model=List[CaseResponse])
async def list_cases(db: AsyncSession = DbSession, current_user: dict = CurrentUser):
    return await CaseService.get_user_cases(db, current_user["sub"])

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: UUID, db: AsyncSession = DbSession, current_user: dict = CurrentUser):
    return await CaseService.get_case_by_id(db, case_id, current_user["sub"])

@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: UUID, db: AsyncSession = DbSession, current_user: dict = CurrentUser):
    await CaseService.delete_case(db, case_id, current_user["sub"])


# --- DOCUMENTS ---

@router.get("/{case_id}/documents", response_model=List[DocumentResponse])
async def list_documents(case_id: UUID, db: AsyncSession = DbSession, current_user: dict = CurrentUser):
    return await DocumentService.get_case_documents(db, case_id, current_user["sub"])

@router.post("/{case_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: UUID, 
    file: UploadFile = File(...), 
    document_type: str = Form(None),
    version: str = Form(None),
    db: AsyncSession = DbSession, 
    current_user: dict = CurrentUser
):
    # 1. Authorize: Ensure user owns this case
    await CaseService.get_case_by_id(db, case_id, current_user["sub"])

    # 2. Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")
    
    # 3. Read file into memory (for huge files, streaming is better, but this is simple)
    file_bytes = await file.read()
    
    # 4. Generate a unique ID and storage path
    document_id = uuid.uuid4()
    storage_path = f"{case_id}/{document_id}.pdf"
    
    # 5. Upload to Supabase Storage
    try:
        await storage_service.upload_file(file_bytes, storage_path, file.content_type)
    except Exception as e:
        # Ideally log this error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload to storage")

    # 6. Save metadata to Postgres
    document = await DocumentService.create_document_record(
        db=db,
        case_id=case_id,
        filename=file.filename,
        storage_path=storage_path,
        content_type=file.content_type,
        size_bytes=len(file_bytes),
        document_type=document_type,
        version=version
    )
    
    # 7. Semantic Processing Pipeline
    from src.api.services.pipeline import DocumentPipelineService
    
    # We await this directly, but in a future iteration, this is the exact line 
    # you would offload to a background task (e.g. Celery).
    await DocumentPipelineService.process_document(db, document.id, file_bytes)

    return document

@router.delete("/{case_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    case_id: UUID, 
    document_id: UUID, 
    db: AsyncSession = DbSession, 
    current_user: dict = CurrentUser
):
    # 1. Fetch document and authorize
    doc = await DocumentService.get_document_by_id(db, document_id, case_id, current_user["sub"])
    
    # 2. Delete from Supabase Storage
    await storage_service.delete_file(doc.storage_path)
    
    # 3. Delete from Postgres
    await DocumentService.delete_document_record(db, doc)


# --- SEMANTIC SEARCH ---

@router.post("/{case_id}/search", response_model=SearchResponse)
async def semantic_search(
    case_id: UUID, 
    request: SearchRequest,
    db: AsyncSession = DbSession, 
    current_user: dict = CurrentUser
):
    from src.api.services.search import SearchService
    try:
        results = await SearchService.semantic_search(
            db=db, 
            case_id=case_id, 
            user_id=current_user["sub"], 
            query=request.query, 
            top_k=request.top_k
        )
        return SearchResponse(results=results)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed")


# --- RAG CHAT ---

@router.post("/{case_id}/chat", response_model=ChatResponse)
async def rag_chat(
    case_id: UUID,
    request: ChatRequest,
    db: AsyncSession = DbSession,
    current_user: dict = CurrentUser,
):
    """Answer a question from case-scoped retrieval evidence using Gemini via LiteLLM."""
    try:
        result = await RAGChatService().chat(
            db=db,
            case_id=case_id,
            user_id=current_user["sub"],
            question=request.question,
            top_k=request.top_k,
            conversation_id=request.conversation_id,
        )
        return ChatResponse(
            conversation_id=result.conversation_id,
            message_id=result.message_id,
            answer=result.answer,
            sources=result.sources,
            citations=result.citations,
            prompt_template_version=result.prompt_template_version,
        )
    except NoGroundedContextError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LLMProviderError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The language model is temporarily unavailable",
        )
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Chat failed")
