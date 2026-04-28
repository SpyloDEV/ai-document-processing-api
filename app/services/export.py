import csv
from io import StringIO
from typing import Any


class ExportService:
    def to_json(self, extracted_data: dict[str, Any]) -> dict[str, Any]:
        return extracted_data

    def to_csv(self, extracted_data: dict[str, Any]) -> str:
        output = StringIO()
        fieldnames = [
            "document_type",
            "vendor_name",
            "customer_name",
            "invoice_number",
            "invoice_date",
            "due_date",
            "total_amount",
            "currency",
            "tax_amount",
            "line_item_description",
            "line_item_quantity",
            "line_item_unit_price",
            "line_item_amount",
            "confidence_score",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        line_items = extracted_data.get("line_items") or [{}]
        for item in line_items:
            writer.writerow(
                {
                    "document_type": extracted_data.get("document_type"),
                    "vendor_name": extracted_data.get("vendor_name"),
                    "customer_name": extracted_data.get("customer_name"),
                    "invoice_number": extracted_data.get("invoice_number"),
                    "invoice_date": extracted_data.get("invoice_date"),
                    "due_date": extracted_data.get("due_date"),
                    "total_amount": extracted_data.get("total_amount"),
                    "currency": extracted_data.get("currency"),
                    "tax_amount": extracted_data.get("tax_amount"),
                    "line_item_description": item.get("description"),
                    "line_item_quantity": item.get("quantity"),
                    "line_item_unit_price": item.get("unit_price"),
                    "line_item_amount": item.get("amount"),
                    "confidence_score": extracted_data.get("confidence_score"),
                }
            )
        return output.getvalue()
