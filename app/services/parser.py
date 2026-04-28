import csv
from dataclasses import dataclass, field
from pathlib import Path

from app.models.document import Document


@dataclass
class ParsedDocument:
    text: str
    rows: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


class DocumentParser:
    def parse(self, document: Document) -> ParsedDocument:
        path = Path(document.storage_path)
        extension = document.file_extension.lower()

        if extension == "csv":
            return self._parse_csv(path, document)
        if extension == "txt":
            return self._parse_text(path, document)
        return self._parse_binary(path, document)

    def _parse_text(self, path: Path, document: Document) -> ParsedDocument:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return ParsedDocument(text=text, metadata=self._metadata(document))

    def _parse_csv(self, path: Path, document: Document) -> ParsedDocument:
        text = path.read_text(encoding="utf-8", errors="ignore")
        rows = list(csv.DictReader(text.splitlines()))
        return ParsedDocument(text=text, rows=rows, metadata=self._metadata(document))

    def _parse_binary(self, path: Path, document: Document) -> ParsedDocument:
        sample = path.read_bytes()[:4096].decode("utf-8", errors="ignore")
        metadata = self._metadata(document)
        metadata["binary_sample_size"] = str(len(sample))
        return ParsedDocument(text=sample, metadata=metadata)

    def _metadata(self, document: Document) -> dict[str, str]:
        return {
            "filename": document.original_filename,
            "extension": document.file_extension,
            "content_type": document.content_type,
        }
