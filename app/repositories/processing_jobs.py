from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_job import ProcessingJob, ProcessingJobStatus


class ProcessingJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, job_id: str) -> ProcessingJob | None:
        return await self.session.get(ProcessingJob, job_id)

    async def create(
        self,
        *,
        document_id: str,
        job_type: str,
        payload: dict,
    ) -> ProcessingJob:
        job = ProcessingJob(
            document_id=document_id,
            job_type=job_type,
            payload=payload,
            status=ProcessingJobStatus.QUEUED,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def set_status(
        self,
        job: ProcessingJob,
        *,
        status: ProcessingJobStatus,
        result: dict | None = None,
        error: str | None = None,
        celery_task_id: str | None = None,
    ) -> ProcessingJob:
        job.status = status
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        if celery_task_id is not None:
            job.celery_task_id = celery_task_id
        await self.session.flush()
        return job
