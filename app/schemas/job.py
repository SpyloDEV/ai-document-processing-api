from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.processing_job import ProcessingJobStatus


class ProcessingJobRead(BaseModel):
    id: str
    document_id: str
    job_type: str
    status: ProcessingJobStatus
    celery_task_id: str | None
    payload: dict
    result: dict | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
