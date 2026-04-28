from httpx import AsyncClient

from tests.conftest import register_user, upload_invoice_text


async def test_upload_rejects_unsupported_file_type(
    client: AsyncClient,
    auth_headers,
) -> None:
    auth = await register_user(client)

    response = await client.post(
        "/api/v1/documents/upload",
        headers=auth_headers(auth["access_token"]),
        files={"file": ("payload.exe", b"not allowed", "application/octet-stream")},
    )

    assert response.status_code == 422


async def test_upload_rejects_empty_files(client: AsyncClient, auth_headers) -> None:
    auth = await register_user(client)

    response = await client.post(
        "/api/v1/documents/upload",
        headers=auth_headers(auth["access_token"]),
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 422


async def test_document_upload_completes_mock_processing(
    client: AsyncClient,
) -> None:
    auth = await register_user(client)
    uploaded = await upload_invoice_text(client, auth["access_token"])

    assert uploaded["document"]["status"] == "completed"
    assert uploaded["processing_job_id"]
    assert uploaded["document"]["original_filename"] == "invoice-1001.txt"
