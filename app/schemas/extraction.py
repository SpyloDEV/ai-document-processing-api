from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class LineItem(BaseModel):
    description: str
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class ExtractedData(BaseModel):
    document_type: str | None = None
    vendor_name: str | None = None
    customer_name: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    total_amount: float | None = None
    currency: str | None = None
    tax_amount: float | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    confidence_score: float = 0.0


class ExtractionResultRead(BaseModel):
    id: str
    document_id: str
    extracted_data: ExtractedData
    confidence_score: float
    extractor_version: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
