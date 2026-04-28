from sqlalchemy import JSON, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ValidationResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "validation_results"
    __table_args__ = (UniqueConstraint("document_id", name="uq_validation_document"),)

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    is_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    missing_fields: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    document = relationship("Document", back_populates="validation_result")
