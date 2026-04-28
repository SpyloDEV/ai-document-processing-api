from fastapi import APIRouter, File, Query, Response, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.models.document import DocumentStatus
from app.schemas.common import Message, Page
from app.schemas.document import DocumentRead, DocumentUploadResponse
from app.schemas.extraction import ExtractedData, ExtractionResultRead
from app.schemas.validation import ValidationResultRead
from app.services.documents import DocumentService
from app.services.export import ExportService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    current_user: CurrentUser,
    session: DbSession,
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    uploaded = await DocumentService(session).upload_document(
        owner_id=current_user.id,
        upload=file,
    )
    await session.commit()
    await session.refresh(uploaded.document)
    return DocumentUploadResponse(
        document=uploaded.document,
        processing_job_id=uploaded.job.id,
    )


@router.get("", response_model=Page[DocumentRead])
async def list_documents(
    current_user: CurrentUser,
    session: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: DocumentStatus | None = Query(default=None, alias="status"),
) -> Page[DocumentRead]:
    documents, total = await DocumentService(session).list_documents(
        owner_id=current_user.id,
        limit=limit,
        offset=offset,
        status=status_filter,
    )
    return Page(items=documents, total=total, limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: str,
    current_user: CurrentUser,
    session: DbSession,
) -> DocumentRead:
    return await DocumentService(session).get_document(
        document_id=document_id,
        owner_id=current_user.id,
    )


@router.get("/{document_id}/result", response_model=ExtractionResultRead)
async def get_extraction_result(
    document_id: str,
    current_user: CurrentUser,
    session: DbSession,
) -> ExtractionResultRead:
    return await DocumentService(session).get_extraction_result(
        document_id=document_id,
        owner_id=current_user.id,
    )


@router.get("/{document_id}/validation", response_model=ValidationResultRead)
async def get_validation_result(
    document_id: str,
    current_user: CurrentUser,
    session: DbSession,
) -> ValidationResultRead:
    return await DocumentService(session).get_validation_result(
        document_id=document_id,
        owner_id=current_user.id,
    )


@router.get("/{document_id}/export/json", response_model=ExtractedData)
async def export_json(
    document_id: str,
    current_user: CurrentUser,
    session: DbSession,
) -> dict:
    result = await DocumentService(session).get_extraction_result(
        document_id=document_id,
        owner_id=current_user.id,
    )
    return ExportService().to_json(result.extracted_data)


@router.get("/{document_id}/export/csv")
async def export_csv(
    document_id: str,
    current_user: CurrentUser,
    session: DbSession,
) -> Response:
    result = await DocumentService(session).get_extraction_result(
        document_id=document_id,
        owner_id=current_user.id,
    )
    csv_content = ExportService().to_csv(result.extracted_data)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{document_id}.csv"'},
    )


@router.delete("/{document_id}", response_model=Message)
async def delete_document(
    document_id: str,
    current_user: CurrentUser,
    session: DbSession,
) -> Message:
    await DocumentService(session).delete_document(
        document_id=document_id,
        owner_id=current_user.id,
    )
    await session.commit()
    return Message(message="Document deleted.")
