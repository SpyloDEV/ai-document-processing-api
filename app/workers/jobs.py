import asyncio

from app.db.session import AsyncSessionLocal
from app.services.processing import ProcessingService
from app.workers.celery_app import celery_app


@celery_app.task(name="documents.process_document")
def process_document_task(document_id: str, job_id: str) -> None:
    asyncio.run(_process_document(document_id=document_id, job_id=job_id))


async def _process_document(*, document_id: str, job_id: str) -> None:
    async with AsyncSessionLocal() as session:
        await ProcessingService(session).process_document(
            document_id=document_id,
            job_id=job_id,
            raise_errors=True,
        )
        await session.commit()
