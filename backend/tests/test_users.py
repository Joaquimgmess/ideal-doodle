import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.anyio

API = settings.API_V1_STR


async def test_read_user_me(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.get(f"{API}/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data


async def test_update_user_me(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.patch(
        f"{API}/users/me",
        headers=auth_headers,
        json={"full_name": "Updated Name"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


async def test_update_password(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.patch(
        f"{API}/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "testpassword123",
            "new_password": "newpassword456",
        },
    )
    assert response.status_code == 200

    login = await client.post(
        f"{API}/login/access-token",
        data={"username": "test@example.com", "password": "newpassword456"},
    )
    assert login.status_code == 200


async def test_update_password_wrong_current(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.patch(
        f"{API}/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        },
    )
    assert response.status_code == 400


async def test_list_users_superuser(
    client: AsyncClient, superuser_headers: dict[str, str]
):
    response = await client.get(f"{API}/users/", headers=superuser_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] >= 1


async def test_list_users_regular_user_forbidden(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.get(f"{API}/users/", headers=auth_headers)
    assert response.status_code == 403


async def test_delete_user_me(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.delete(f"{API}/users/me", headers=auth_headers)
    assert response.status_code == 200

    login = await client.post(
        f"{API}/login/access-token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert login.status_code == 400


async def test_delete_superuser_forbidden(
    client: AsyncClient, superuser_headers: dict[str, str]
):
    response = await client.delete(f"{API}/users/me", headers=superuser_headers)
    assert response.status_code == 403
