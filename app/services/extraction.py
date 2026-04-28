import re
from datetime import date
from typing import Any

from app.services.parser import ParsedDocument


class MockExtractionService:
    def extract(self, parsed: ParsedDocument) -> dict[str, Any]:
        if parsed.rows:
            data = self._extract_from_csv(parsed)
        else:
            data = self._extract_from_text(parsed.text, parsed.metadata)
        data["confidence_score"] = self._score(data)
        return data

    def _extract_from_csv(self, parsed: ParsedDocument) -> dict[str, Any]:
        first_row = parsed.rows[0] if parsed.rows else {}
        line_items = []
        total_amount = 0.0
        currency = self._pick(first_row, "currency", "curr") or "USD"

        for row in parsed.rows:
            amount = self._to_float(self._pick(row, "amount", "total", "line_total"))
            if amount is not None:
                total_amount += amount
            line_items.append(
                {
                    "description": self._pick(row, "description", "item", "name")
                    or "Imported CSV row",
                    "quantity": self._to_float(self._pick(row, "quantity", "qty")),
                    "unit_price": self._to_float(
                        self._pick(row, "unit_price", "price", "rate")
                    ),
                    "amount": amount,
                }
            )

        return {
            "document_type": "invoice",
            "vendor_name": self._pick(first_row, "vendor", "vendor_name", "supplier"),
            "customer_name": self._pick(
                first_row, "customer", "customer_name", "client"
            ),
            "invoice_number": self._pick(
                first_row, "invoice_number", "invoice", "number"
            ),
            "invoice_date": self._parse_date(
                self._pick(first_row, "invoice_date", "date")
            ),
            "due_date": self._parse_date(self._pick(first_row, "due_date", "due")),
            "total_amount": round(total_amount, 2) if total_amount else None,
            "currency": currency,
            "tax_amount": self._to_float(self._pick(first_row, "tax", "tax_amount")),
            "line_items": line_items,
        }

    def _extract_from_text(self, text: str, metadata: dict[str, str]) -> dict[str, Any]:
        lower_name = metadata.get("filename", "").lower()
        document_type = (
            "invoice"
            if "invoice" in text.lower() or "invoice" in lower_name
            else "document"
        )
        total, currency = self._extract_money(text)
        return {
            "document_type": document_type,
            "vendor_name": self._match_label(text, "vendor")
            or self._match_label(text, "supplier"),
            "customer_name": self._match_label(text, "customer")
            or self._match_label(text, "client"),
            "invoice_number": self._match_invoice_number(text),
            "invoice_date": self._parse_date(self._match_label(text, "invoice date")),
            "due_date": self._parse_date(self._match_label(text, "due date")),
            "total_amount": total,
            "currency": currency,
            "tax_amount": self._to_float(self._match_label(text, "tax")),
            "line_items": self._mock_line_items(text),
        }

    def _score(self, data: dict[str, Any]) -> float:
        fields = [
            "document_type",
            "vendor_name",
            "invoice_number",
            "invoice_date",
            "total_amount",
            "currency",
        ]
        filled = sum(1 for field in fields if data.get(field))
        score = 0.35 + (filled / len(fields)) * 0.55
        if data.get("line_items"):
            score += 0.08
        return min(round(score, 2), 0.98)

    def _match_label(self, text: str, label: str) -> str | None:
        pattern = rf"{label}\s*[:#-]\s*(.+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        return match.group(1).strip().splitlines()[0][:160]

    def _match_invoice_number(self, text: str) -> str | None:
        match = re.search(
            r"invoice\s*(number|no\.?|#)\s*[:#-]?\s*([A-Z0-9-]+)",
            text,
            re.IGNORECASE,
        )
        return match.group(2) if match else None

    def _extract_money(self, text: str) -> tuple[float | None, str | None]:
        money_pattern = (
            r"(total|amount due)\s*[:#-]?\s*"
            r"(USD|EUR|GBP|\$|€|£)?\s*([0-9][0-9,]*\.?[0-9]*)"
        )
        match = re.search(
            money_pattern,
            text,
            re.IGNORECASE,
        )
        if not match:
            return None, None
        currency = {"$": "USD", "€": "EUR", "£": "GBP"}.get(
            match.group(2), match.group(2)
        )
        return self._to_float(match.group(3)), currency or "USD"

    def _mock_line_items(self, text: str) -> list[dict[str, float | str | None]]:
        if not text.strip():
            return []
        return [
            {
                "description": "Detected document services",
                "quantity": 1.0,
                "unit_price": None,
                "amount": None,
            }
        ]

    def _pick(self, row: dict[str, str], *keys: str) -> str | None:
        normalized = {key.lower().strip(): value for key, value in row.items()}
        for key in keys:
            value = normalized.get(key)
            if value not in {None, ""}:
                return value
        return None

    def _to_float(self, value: str | None) -> float | None:
        if value is None:
            return None
        cleaned = re.sub(r"[^0-9.\-]", "", value)
        if cleaned in {"", ".", "-"}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _parse_date(self, value: str | None) -> str | None:
        if not value:
            return None
        match = re.search(r"(\d{4}-\d{2}-\d{2})", value)
        if not match:
            return None
        try:
            return date.fromisoformat(match.group(1)).isoformat()
        except ValueError:
            return None
