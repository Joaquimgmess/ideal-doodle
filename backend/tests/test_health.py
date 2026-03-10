import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.anyio

API = settings.API_V1_STR


async def test_health_check(client: AsyncClient):
    response = await client.get(f"{API}/utils/health-check/")
    assert response.status_code == 200
    assert response.json() == {"alive": True}


async def test_readiness_check(client: AsyncClient):
    response = await client.get(f"{API}/utils/ready/")
    assert response.status_code == 200
    data = response.json()
    assert data["db"] is True
    assert "scheduler" in data
