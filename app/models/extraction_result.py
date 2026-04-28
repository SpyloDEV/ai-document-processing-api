from sqlalchemy import JSON, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExtractionResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extraction_results"
    __table_args__ = (UniqueConstraint("document_id", name="uq_extraction_document"),)

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    extracted_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    extractor_version: Mapped[str] = mapped_column(default="mock-v1", nullable=False)

    document = relationship("Document", back_populates="extraction_result")
