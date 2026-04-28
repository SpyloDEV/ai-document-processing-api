from httpx import AsyncClient

from tests.conftest import register_user, upload_invoice_text


async def test_document_list_supports_pagination_and_status_filter(
    client: AsyncClient,
    auth_headers,
) -> None:
    auth = await register_user(client)
    await upload_invoice_text(client, auth["access_token"], filename="invoice-a.txt")
    await upload_invoice_text(client, auth["access_token"], filename="invoice-b.txt")

    response = await client.get(
        "/api/v1/documents",
        headers=auth_headers(auth["access_token"]),
        params={"status": "completed", "limit": 1, "offset": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["status"] == "completed"


async def test_users_can_only_access_their_own_documents(
    client: AsyncClient,
    auth_headers,
) -> None:
    owner = await register_user(client, email="owner@example.com")
    outsider = await register_user(client, email="outsider@example.com")
    uploaded = await upload_invoice_text(client, owner["access_token"])
    document_id = uploaded["document"]["id"]

    get_response = await client.get(
        f"/api/v1/documents/{document_id}",
        headers=auth_headers(outsider["access_token"]),
    )
    result_response = await client.get(
        f"/api/v1/documents/{document_id}/result",
        headers=auth_headers(outsider["access_token"]),
    )
    delete_response = await client.delete(
        f"/api/v1/documents/{document_id}",
        headers=auth_headers(outsider["access_token"]),
    )

    assert get_response.status_code == 404
    assert result_response.status_code == 404
    assert delete_response.status_code == 404
