from httpx import AsyncClient

from tests.conftest import register_user


async def test_register_login_and_current_user(
    client: AsyncClient,
    auth_headers,
) -> None:
    auth = await register_user(client, email="founder@example.com")

    me = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers(auth["access_token"]),
    )
    assert me.status_code == 200
    assert me.json()["email"] == "founder@example.com"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "founder@example.com", "password": "strong-password"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


async def test_duplicate_registration_is_rejected(client: AsyncClient) -> None:
    await register_user(client, email="duplicate@example.com")

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "strong-password",
            "full_name": "Duplicate",
        },
    )

    assert duplicate.status_code == 409
