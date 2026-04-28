from typing import Any


class ValidationService:
    important_fields = ["document_type", "vendor_name", "total_amount", "currency"]

    def validate(self, extracted_data: dict[str, Any]) -> dict[str, Any]:
        missing_fields = [
            field for field in self.important_fields if not extracted_data.get(field)
        ]
        warnings = []

        if not extracted_data.get("invoice_number"):
            warnings.append("Invoice number was not detected.")
        if not extracted_data.get("invoice_date"):
            warnings.append("Invoice date was not detected.")
        if not extracted_data.get("line_items"):
            warnings.append("No line items were detected.")

        confidence_score = float(extracted_data.get("confidence_score") or 0.0)
        if confidence_score < 0.7:
            warnings.append("Extraction confidence is below the review threshold.")

        total_amount = extracted_data.get("total_amount")
        tax_amount = extracted_data.get("tax_amount")
        if (
            total_amount is not None
            and tax_amount is not None
            and tax_amount > total_amount
        ):
            warnings.append("Tax amount is greater than the total amount.")

        adjusted_score = max(
            round(confidence_score - len(missing_fields) * 0.08, 2), 0.0
        )
        return {
            "is_valid": len(missing_fields) == 0 and adjusted_score >= 0.65,
            "missing_fields": missing_fields,
            "warnings": warnings,
            "confidence_score": adjusted_score,
        }
