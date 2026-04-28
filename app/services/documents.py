from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.document import Document, DocumentStatus
from app.models.extraction_result import ExtractionResult
from app.models.processing_job import ProcessingJob
from app.models.validation_result import ValidationResult
from app.repositories.documents import DocumentRepository
from app.repositories.extraction_results import ExtractionResultRepository
from app.repositories.validation_results import ValidationResultRepository
from app.services.processing import ProcessingService
from app.services.storage import StorageService


class DocumentUpload:
    def __init__(self, *, document: Document, job: ProcessingJob) -> None:
        self.document = document
        self.job = job


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.extraction_results = ExtractionResultRepository(session)
        self.validation_results = ValidationResultRepository(session)
        self.storage = StorageService()
        self.processing = ProcessingService(session)

    async def upload_document(
        self, *, owner_id: str, upload: UploadFile
    ) -> DocumentUpload:
        content = await upload.read()
        stored_upload = self.storage.save_upload(
            filename=upload.filename or "",
            content_type=upload.content_type,
            content=content,
        )
        document = await self.documents.create(
            owner_id=owner_id,
            original_filename=stored_upload.original_filename,
            stored_filename=stored_upload.stored_filename,
            storage_path=stored_upload.storage_path,
            content_type=stored_upload.content_type,
            file_extension=stored_upload.file_extension,
            file_size=stored_upload.file_size,
            checksum_sha256=stored_upload.checksum_sha256,
        )
        job = await self.processing.enqueue_document_processing(document_id=document.id)
        return DocumentUpload(document=document, job=job)

    async def list_documents(
        self,
        *,
        owner_id: str,
        limit: int,
        offset: int,
        status: DocumentStatus | None,
    ) -> tuple[list[Document], int]:
        return await self.documents.list_for_user(
            owner_id=owner_id,
            limit=limit,
            offset=offset,
            status=status,
        )

    async def get_document(self, *, document_id: str, owner_id: str) -> Document:
        document = await self.documents.get_for_user(
            document_id=document_id,
            owner_id=owner_id,
        )
        if document is None:
            raise NotFoundError("Document not found.")
        return document

    async def get_extraction_result(
        self,
        *,
        document_id: str,
        owner_id: str,
    ) -> ExtractionResult:
        document = await self.get_document(document_id=document_id, owner_id=owner_id)
        result = await self.extraction_results.get_for_document(document.id)
        if result is None:
            raise NotFoundError("Extraction result is not available yet.")
        return result

    async def get_validation_result(
        self,
        *,
        document_id: str,
        owner_id: str,
    ) -> ValidationResult:
        document = await self.get_document(document_id=document_id, owner_id=owner_id)
        result = await self.validation_results.get_for_document(document.id)
        if result is None:
            raise NotFoundError("Validation result is not available yet.")
        return result

    async def delete_document(self, *, document_id: str, owner_id: str) -> None:
        document = await self.get_document(document_id=document_id, owner_id=owner_id)
        storage_path = document.storage_path
        await self.documents.delete(document)
        self.storage.delete_file(storage_path)
