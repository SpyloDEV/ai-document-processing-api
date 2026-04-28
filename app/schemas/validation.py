from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ValidationResultRead(BaseModel):
    id: str
    document_id: str
    is_valid: bool
    missing_fields: list[str]
    warnings: list[str]
    confidence_score: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
