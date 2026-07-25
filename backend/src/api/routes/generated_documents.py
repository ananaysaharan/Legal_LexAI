from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.security import get_current_user
from src.api.db.database import get_db
from src.api.schemas.exporting import ExportRequest
from src.api.schemas.generated_documents import (
    DocumentEditRequest,
    DocumentExportMetadata,
    DocumentSaveRequest,
    GeneratedDocumentCreate,
    GeneratedDocumentResponse,
)
from src.api.schemas.jobs import JobResponse
from src.api.services.document_workspace import DocumentWorkspaceService
from src.api.services.generated_documents import GeneratedDocumentService
from src.api.services.task_dispatcher import TaskDispatcher

router = APIRouter()
service = GeneratedDocumentService()
workspace = DocumentWorkspaceService()
dispatcher = TaskDispatcher()


@router.post("/", response_model=GeneratedDocumentResponse, status_code=status.HTTP_201_CREATED)
async def generate_document(
    request: GeneratedDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> GeneratedDocumentResponse:
    try:
        return await service.generate(db, current_user["sub"], request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def queue_document_generation(
    request: GeneratedDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> JobResponse:
    return await dispatcher.enqueue_document_generation(
        db, current_user["sub"], request.case_id, {"request": request.model_dump(mode="json")}
    )


@router.get("/cases/{case_id}", response_model=list[GeneratedDocumentResponse])
async def list_generated_documents(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[GeneratedDocumentResponse]:
    return await service.list_for_case(db, case_id, current_user["sub"])


@router.get("/{document_id}", response_model=GeneratedDocumentResponse)
async def open_generated_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> GeneratedDocumentResponse:
    return await workspace.get_document(db, document_id, current_user["sub"])


@router.post("/{document_id}/edit", response_model=GeneratedDocumentResponse, status_code=status.HTTP_201_CREATED)
async def edit_generated_document(
    document_id: UUID,
    request: DocumentEditRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> GeneratedDocumentResponse:
    try:
        return await workspace.edit_with_ai(db, document_id, current_user["sub"], request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{document_id}/save", response_model=GeneratedDocumentResponse, status_code=status.HTTP_201_CREATED)
async def save_generated_document_edit(
    document_id: UUID,
    request: DocumentSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> GeneratedDocumentResponse:
    return await workspace.save_edit(db, document_id, current_user["sub"], request)


@router.get("/{document_id}/versions", response_model=list[GeneratedDocumentResponse])
async def list_document_versions(
    document_id: UUID,
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[GeneratedDocumentResponse]:
    return await workspace.list_versions(db, document_id, current_user["sub"], include_deleted)


@router.post("/{document_id}/restore", response_model=GeneratedDocumentResponse, status_code=status.HTTP_201_CREATED)
async def restore_document_version(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> GeneratedDocumentResponse:
    return await workspace.restore(db, document_id, current_user["sub"])


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_generated_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> None:
    await workspace.soft_delete(db, document_id, current_user["sub"])


@router.get("/{document_id}/export-metadata", response_model=DocumentExportMetadata)
async def get_document_export_metadata(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> DocumentExportMetadata:
    return await workspace.export_metadata(db, document_id, current_user["sub"])


@router.post("/{document_id}/exports", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def queue_document_export(
    document_id: UUID,
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> JobResponse:
    document = await workspace.get_document(db, document_id, current_user["sub"])
    return await dispatcher.enqueue_export(
        db,
        current_user["sub"],
        document.case_id,
        {"document_id": str(document_id), "format": request.format.value, "include_citations": request.include_citations},
    )
