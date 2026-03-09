from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models import KPIHistory

pytestmark = pytest.mark.anyio

API = settings.API_V1_STR


def _kpi(nome: str, valor: int, hour: int) -> KPIHistory:
    """Helper para criar KPI com timestamp determinístico."""
    return KPIHistory(
        nome_kpi=nome,
        valor=valor,
        data_registro=datetime(2026, 1, 1, hour, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# GET /kpis/
# ---------------------------------------------------------------------------


async def test_list_kpis_empty(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/kpis/", headers=api_key_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["count"] == 0


async def test_list_kpis_returns_data(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    session.add(_kpi("total_voluntarios", 42, hour=1))
    session.add(_kpi("total_voluntarios", 50, hour=2))
    await session.commit()

    response = await client.get(f"{API}/kpis/", headers=api_key_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["data"]) == 2
    # mais recente primeiro
    assert data["data"][0]["valor"] == 50
    assert data["data"][1]["valor"] == 42


async def test_list_kpis_order_desc(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    session.add(_kpi("total_voluntarios", 10, hour=1))
    session.add(_kpi("total_voluntarios", 20, hour=2))
    session.add(_kpi("total_voluntarios", 30, hour=3))
    await session.commit()

    response = await client.get(f"{API}/kpis/", headers=api_key_headers)
    valores = [item["valor"] for item in response.json()["data"]]
    assert valores == [30, 20, 10]


async def test_list_kpis_filter_by_nome(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    session.add(_kpi("total_voluntarios", 10, hour=1))
    session.add(_kpi("total_pedidos", 99, hour=2))
    await session.commit()

    response = await client.get(
        f"{API}/kpis/",
        headers=api_key_headers,
        params={"nome": "total_pedidos"},
    )
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["nome_kpi"] == "total_pedidos"


async def test_list_kpis_pagination(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    for h in range(5):
        session.add(_kpi("total_voluntarios", h * 10, hour=h))
    await session.commit()

    response = await client.get(
        f"{API}/kpis/",
        headers=api_key_headers,
        params={"skip": 0, "limit": 2},
    )
    data = response.json()
    assert data["count"] == 5
    assert len(data["data"]) == 2


# ---------------------------------------------------------------------------
# GET /kpis/ultimo
# ---------------------------------------------------------------------------


async def test_ultimo_kpi(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    session.add(_kpi("total_voluntarios", 42, hour=1))
    session.add(_kpi("total_voluntarios", 99, hour=2))
    await session.commit()

    response = await client.get(
        f"{API}/kpis/ultimo",
        headers=api_key_headers,
        params={"nome": "total_voluntarios"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome_kpi"] == "total_voluntarios"
    assert data["valor"] == 99


async def test_ultimo_kpi_by_nome(
    client: AsyncClient, session: AsyncSession, api_key_headers: dict[str, str]
):
    session.add(_kpi("total_voluntarios", 42, hour=1))
    session.add(_kpi("total_pedidos", 100, hour=2))
    await session.commit()

    response = await client.get(
        f"{API}/kpis/ultimo",
        headers=api_key_headers,
        params={"nome": "total_pedidos"},
    )
    assert response.status_code == 200
    assert response.json()["valor"] == 100


async def test_ultimo_kpi_not_found(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    response = await client.get(
        f"{API}/kpis/ultimo",
        headers=api_key_headers,
        params={"nome": "inexistente"},
    )
    assert response.status_code == 404


async def test_ultimo_kpi_nome_required(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    response = await client.get(f"{API}/kpis/ultimo", headers=api_key_headers)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Sem API Key
# ---------------------------------------------------------------------------


async def test_list_kpis_no_api_key(client: AsyncClient):
    response = await client.get(f"{API}/kpis/")
    assert response.status_code == 422


async def test_ultimo_kpi_no_api_key(client: AsyncClient):
    response = await client.get(f"{API}/kpis/ultimo")
    assert response.status_code == 422
