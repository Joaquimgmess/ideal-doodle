import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.anyio


async def test_signup_success(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/users/signup",
        json={
            "email": "new@example.com",
            "password": "newpassword123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.usefixtures("test_user")
async def test_signup_duplicate_email(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/users/signup",
        json={
            "email": "test@example.com",
            "password": "anotherpassword123",
        },
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("test_user")
async def test_login_success(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.usefixtures("test_user")
async def test_login_wrong_password(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 400


async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "nobody@example.com", "password": "whatever123"},
    )
    assert response.status_code == 400


async def test_test_token(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


async def test_test_token_no_auth(client: AsyncClient):
    response = await client.post(f"{settings.API_V1_STR}/login/test-token")
    assert response.status_code == 401
