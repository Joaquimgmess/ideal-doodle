import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models import KPIHistory

pytestmark = pytest.mark.anyio

API = settings.API_V1_STR


# ---------------------------------------------------------------------------
# GET /kpis/
# ---------------------------------------------------------------------------


async def test_list_kpis_empty(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/kpis/", headers=api_key_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_kpis_returns_data(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    session.add(KPIHistory(nome_kpi="total_voluntarios", valor=42))
    session.add(KPIHistory(nome_kpi="total_voluntarios", valor=50))
    await session.commit()

    response = await client.get(f"{API}/kpis/", headers=api_key_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # mais recente primeiro
    assert data[0]["valor"] == 50
    assert data[1]["valor"] == 42


async def test_list_kpis_order_desc(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    session.add(KPIHistory(nome_kpi="total_voluntarios", valor=10))
    session.add(KPIHistory(nome_kpi="total_voluntarios", valor=20))
    session.add(KPIHistory(nome_kpi="total_voluntarios", valor=30))
    await session.commit()

    response = await client.get(f"{API}/kpis/", headers=api_key_headers)
    data = response.json()
    valores = [item["valor"] for item in data]
    assert valores == [30, 20, 10]


# ---------------------------------------------------------------------------
# GET /kpis/ultimo
# ---------------------------------------------------------------------------


async def test_ultimo_kpi_empty(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/kpis/ultimo", headers=api_key_headers)
    assert response.status_code == 200
    assert response.json() is None


async def test_ultimo_kpi_default_nome(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    session.add(KPIHistory(nome_kpi="total_voluntarios", valor=42))
    session.add(KPIHistory(nome_kpi="total_voluntarios", valor=99))
    await session.commit()

    response = await client.get(f"{API}/kpis/ultimo", headers=api_key_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["nome_kpi"] == "total_voluntarios"
    assert data["valor"] == 99


async def test_ultimo_kpi_by_nome(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    session.add(KPIHistory(nome_kpi="total_voluntarios", valor=42))
    session.add(KPIHistory(nome_kpi="total_pedidos", valor=100))
    await session.commit()

    response = await client.get(
        f"{API}/kpis/ultimo",
        headers=api_key_headers,
        params={"nome": "total_pedidos"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome_kpi"] == "total_pedidos"
    assert data["valor"] == 100


async def test_ultimo_kpi_nome_not_found(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    response = await client.get(
        f"{API}/kpis/ultimo",
        headers=api_key_headers,
        params={"nome": "inexistente"},
    )
    assert response.status_code == 200
    assert response.json() is None


# ---------------------------------------------------------------------------
# Sem API Key
# ---------------------------------------------------------------------------


async def test_list_kpis_no_api_key(client: AsyncClient):
    response = await client.get(f"{API}/kpis/")
    assert response.status_code == 422


async def test_ultimo_kpi_no_api_key(client: AsyncClient):
    response = await client.get(f"{API}/kpis/ultimo")
    assert response.status_code == 422
