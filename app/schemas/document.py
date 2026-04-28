from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentRead(BaseModel):
    id: str
    owner_id: str
    original_filename: str
    content_type: str
    file_extension: str
    file_size: int
    checksum_sha256: str
    status: DocumentStatus
    failure_reason: str | None
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    document: DocumentRead
    processing_job_id: str
