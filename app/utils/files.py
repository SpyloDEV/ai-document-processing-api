from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".csv", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/csv",
    "text/plain",
    "application/vnd.ms-excel",
}


def normalized_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_allowed_upload(filename: str, content_type: str | None) -> bool:
    extension = normalized_extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        return False
    if content_type in {None, "", "application/octet-stream"}:
        return True
    return content_type in ALLOWED_CONTENT_TYPES
