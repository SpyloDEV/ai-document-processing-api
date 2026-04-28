from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extraction_result import ExtractionResult


class ExtractionResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_document(self, document_id: str) -> ExtractionResult | None:
        result = await self.session.execute(
            select(ExtractionResult).where(ExtractionResult.document_id == document_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        document_id: str,
        extracted_data: dict,
        confidence_score: float,
        extractor_version: str = "mock-v1",
    ) -> ExtractionResult:
        result = await self.get_for_document(document_id)
        if result is None:
            result = ExtractionResult(document_id=document_id)
            self.session.add(result)
        result.extracted_data = extracted_data
        result.confidence_score = confidence_score
        result.extractor_version = extractor_version
        await self.session.flush()
        return result
