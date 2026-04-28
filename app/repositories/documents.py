from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, document_id: str) -> Document | None:
        return await self.session.get(Document, document_id)

    async def get_for_user(self, *, document_id: str, owner_id: str) -> Document | None:
        result = await self.session.execute(
            select(Document)
            .where(Document.id == document_id, Document.owner_id == owner_id)
            .options(
                selectinload(Document.extraction_result),
                selectinload(Document.validation_result),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        owner_id: str,
        limit: int,
        offset: int,
        status: DocumentStatus | None = None,
    ) -> tuple[list[Document], int]:
        filters = [Document.owner_id == owner_id]
        if status is not None:
            filters.append(Document.status == status)

        total = await self.session.scalar(
            select(func.count()).select_from(Document).where(*filters)
        )
        result = await self.session.execute(
            select(Document)
            .where(*filters)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)

    async def create(
        self,
        *,
        owner_id: str,
        original_filename: str,
        stored_filename: str,
        storage_path: str,
        content_type: str,
        file_extension: str,
        file_size: int,
        checksum_sha256: str,
    ) -> Document:
        document = Document(
            owner_id=owner_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=storage_path,
            content_type=content_type,
            file_extension=file_extension,
            file_size=file_size,
            checksum_sha256=checksum_sha256,
            status=DocumentStatus.UPLOADED,
        )
        self.session.add(document)
        await self.session.flush()
        return document

    async def delete(self, document: Document) -> None:
        await self.session.delete(document)
        await self.session.flush()
