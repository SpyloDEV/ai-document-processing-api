from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation_result import ValidationResult


class ValidationResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_document(self, document_id: str) -> ValidationResult | None:
        result = await self.session.execute(
            select(ValidationResult).where(ValidationResult.document_id == document_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        document_id: str,
        is_valid: bool,
        missing_fields: list[str],
        warnings: list[str],
        confidence_score: float,
    ) -> ValidationResult:
        result = await self.get_for_document(document_id)
        if result is None:
            result = ValidationResult(document_id=document_id)
            self.session.add(result)
        result.is_valid = is_valid
        result.missing_fields = missing_fields
        result.warnings = warnings
        result.confidence_score = confidence_score
        await self.session.flush()
        return result
