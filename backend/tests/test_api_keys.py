import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.anyio

API = settings.API_V1_STR


async def test_create_api_key(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        f"{API}/api-keys",
        headers=auth_headers,
        json={"name": "my-key", "description": "Test key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "my-key"
    assert data["is_active"] is True
    assert "key" in data
    assert data["key"].startswith("sos_")


async def test_create_api_key_no_auth(client: AsyncClient):
    response = await client.post(
        f"{API}/api-keys",
        json={"name": "my-key"},
    )
    # API key creation is open (no auth required)
    assert response.status_code == 200


async def test_list_api_keys_superuser(
    client: AsyncClient, superuser_headers: dict[str, str]
):
    response = await client.get(f"{API}/api-keys", headers=superuser_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_list_api_keys_regular_user_forbidden(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.get(f"{API}/api-keys", headers=auth_headers)
    assert response.status_code == 403


async def test_get_my_api_key(client: AsyncClient, auth_headers: dict[str, str]):
    create_resp = await client.post(
        f"{API}/api-keys",
        headers=auth_headers,
        json={"name": "my-key"},
    )
    key_data = create_resp.json()
    prefix = key_data["prefix"]
    plain_key = key_data["key"]

    response = await client.get(
        f"{API}/api-keys/me/{prefix}",
        headers={"X-API-Key": plain_key},
    )
    assert response.status_code == 200
    assert response.json()["prefix"] == prefix


async def test_deactivate_api_key_superuser(
    client: AsyncClient, auth_headers: dict[str, str], superuser_headers: dict[str, str]
):
    create_resp = await client.post(
        f"{API}/api-keys",
        headers=auth_headers,
        json={"name": "to-delete"},
    )
    key_id = create_resp.json()["id"]

    response = await client.delete(
        f"{API}/api-keys/{key_id}",
        headers=superuser_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "API Key desativada"
