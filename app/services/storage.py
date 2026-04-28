import hashlib
from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.utils.files import is_allowed_upload, normalized_extension


class StoredUpload:
    def __init__(
        self,
        *,
        original_filename: str,
        stored_filename: str,
        storage_path: str,
        content_type: str,
        file_extension: str,
        file_size: int,
        checksum_sha256: str,
    ) -> None:
        self.original_filename = original_filename
        self.stored_filename = stored_filename
        self.storage_path = storage_path
        self.content_type = content_type
        self.file_extension = file_extension
        self.file_size = file_size
        self.checksum_sha256 = checksum_sha256


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage_dir = Path(self.settings.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(
        self,
        *,
        filename: str,
        content_type: str | None,
        content: bytes,
    ) -> StoredUpload:
        if not filename:
            raise ValidationAppError("A filename is required.")
        if not is_allowed_upload(filename, content_type):
            raise ValidationAppError(
                "Unsupported file type.",
                extra={
                    "allowed_extensions": [
                        ".pdf",
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".csv",
                        ".txt",
                    ]
                },
            )
        if len(content) == 0:
            raise ValidationAppError("Uploaded file is empty.")
        if len(content) > self.settings.max_upload_size_bytes:
            raise ValidationAppError(
                "Uploaded file is too large.",
                extra={"max_upload_size_mb": self.settings.max_upload_size_mb},
            )

        extension = normalized_extension(filename)
        stored_filename = f"{uuid4()}{extension}"
        storage_path = self.storage_dir / stored_filename
        storage_path.write_bytes(content)

        return StoredUpload(
            original_filename=filename,
            stored_filename=stored_filename,
            storage_path=str(storage_path),
            content_type=content_type or "application/octet-stream",
            file_extension=extension.lstrip("."),
            file_size=len(content),
            checksum_sha256=hashlib.sha256(content).hexdigest(),
        )

    def delete_file(self, storage_path: str) -> None:
        path = Path(storage_path)
        if path.exists() and path.is_file():
            path.unlink()
