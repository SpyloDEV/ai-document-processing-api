import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import DocumentStatus
from app.models.processing_job import ProcessingJob, ProcessingJobStatus
from app.repositories.documents import DocumentRepository
from app.repositories.extraction_results import ExtractionResultRepository
from app.repositories.processing_jobs import ProcessingJobRepository
from app.repositories.validation_results import ValidationResultRepository
from app.services.extraction import MockExtractionService
from app.services.parser import DocumentParser
from app.services.validation import ValidationService

logger = logging.getLogger(__name__)


class ProcessingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.documents = DocumentRepository(session)
        self.jobs = ProcessingJobRepository(session)
        self.extraction_results = ExtractionResultRepository(session)
        self.validation_results = ValidationResultRepository(session)
        self.parser = DocumentParser()
        self.extractor = MockExtractionService()
        self.validator = ValidationService()

    async def enqueue_document_processing(self, *, document_id: str) -> ProcessingJob:
        job = await self.jobs.create(
            document_id=document_id,
            job_type="document_extraction",
            payload={"document_id": document_id},
        )
        if not self.settings.enable_background_jobs:
            await self.process_document(document_id=document_id, job_id=job.id)
            return job

        from app.workers.jobs import process_document_task

        celery_task = process_document_task.apply_async(
            args=[document_id, job.id], countdown=1
        )
        await self.jobs.set_status(
            job,
            status=ProcessingJobStatus.QUEUED,
            celery_task_id=celery_task.id,
        )
        logger.info(
            "Queued document processing job %s for document %s", job.id, document_id
        )
        return job

    async def process_document(
        self,
        *,
        document_id: str,
        job_id: str,
        raise_errors: bool = False,
    ) -> None:
        document = await self.documents.get(document_id)
        job = await self.jobs.get(job_id)
        if document is None or job is None:
            logger.warning("Processing skipped because document or job was not found")
            return

        try:
            document.status = DocumentStatus.PROCESSING
            await self.jobs.set_status(job, status=ProcessingJobStatus.RUNNING)
            await self.session.flush()

            parsed = self.parser.parse(document)
            extracted_data = self.extractor.extract(parsed)
            validation = self.validator.validate(extracted_data)

            await self.extraction_results.upsert(
                document_id=document.id,
                extracted_data=extracted_data,
                confidence_score=extracted_data["confidence_score"],
            )
            await self.validation_results.upsert(
                document_id=document.id,
                is_valid=validation["is_valid"],
                missing_fields=validation["missing_fields"],
                warnings=validation["warnings"],
                confidence_score=validation["confidence_score"],
            )
            document.status = DocumentStatus.COMPLETED
            document.failure_reason = None
            document.processed_at = datetime.now(UTC)
            await self.jobs.set_status(
                job,
                status=ProcessingJobStatus.SUCCEEDED,
                result={"document_status": document.status.value},
            )
            await self.session.flush()
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.failure_reason = str(exc)
            await self.jobs.set_status(
                job,
                status=ProcessingJobStatus.FAILED,
                error=str(exc),
            )
            await self.session.flush()
            logger.exception("Document processing failed for %s", document_id)
            if raise_errors:
                raise
