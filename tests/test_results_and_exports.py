from httpx import AsyncClient

from tests.conftest import register_user, upload_invoice_text


async def test_extraction_result_and_validation_are_available(
    client: AsyncClient,
    auth_headers,
) -> None:
    auth = await register_user(client)
    uploaded = await upload_invoice_text(client, auth["access_token"])
    document_id = uploaded["document"]["id"]

    result = await client.get(
        f"/api/v1/documents/{document_id}/result",
        headers=auth_headers(auth["access_token"]),
    )
    validation = await client.get(
        f"/api/v1/documents/{document_id}/validation",
        headers=auth_headers(auth["access_token"]),
    )

    assert result.status_code == 200
    extracted = result.json()["extracted_data"]
    assert extracted["document_type"] == "invoice"
    assert extracted["vendor_name"] == "Northwind Supplies"
    assert extracted["total_amount"] == 119.0
    assert extracted["currency"] == "EUR"
    assert result.json()["confidence_score"] >= 0.8

    assert validation.status_code == 200
    assert validation.json()["is_valid"] is True
    assert validation.json()["missing_fields"] == []


async def test_json_and_csv_exports(client: AsyncClient, auth_headers) -> None:
    auth = await register_user(client)
    uploaded = await upload_invoice_text(client, auth["access_token"])
    document_id = uploaded["document"]["id"]

    json_export = await client.get(
        f"/api/v1/documents/{document_id}/export/json",
        headers=auth_headers(auth["access_token"]),
    )
    csv_export = await client.get(
        f"/api/v1/documents/{document_id}/export/csv",
        headers=auth_headers(auth["access_token"]),
    )

    assert json_export.status_code == 200
    assert json_export.json()["invoice_number"] == "INV-1001"

    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers["content-type"]
    assert "vendor_name" in csv_export.text
    assert "Northwind Supplies" in csv_export.text
