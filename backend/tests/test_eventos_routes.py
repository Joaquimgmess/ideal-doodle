import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.anyio

API = settings.API_V1_STR


# ---------------------------------------------------------------------------
# CRUD básico
# ---------------------------------------------------------------------------


async def test_list_eventos(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/eventos", headers=api_key_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] == 0


async def test_create_evento(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={
            "tipo": "indicacao_recurso",
            "destinatario": "bonanza",
            "metadados": {
                "referencia_pedido_id": 123,
                "contato_doador": "João 32999999999",
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tipo"] == "indicacao_recurso"
    assert data["destinatario"] == "bonanza"
    assert data["portal_id"] == "test-key"  # remetente = api_key.slug
    assert data["status"] == "aberto"
    assert data["metadados"]["referencia_pedido_id"] == 123


async def test_create_evento_minimal(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    response = await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "bonanza"},
    )
    assert response.status_code == 201
    assert response.json()["metadados"] == {}


# ---------------------------------------------------------------------------
# PUT / PATCH — só remetente pode alterar
# ---------------------------------------------------------------------------


async def test_update_evento(client: AsyncClient, api_key_headers: dict[str, str]):
    create = await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "bonanza"},
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"{API}/eventos/{item_id}",
        headers=api_key_headers,
        json={"status": "atendido"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "atendido"


async def test_patch_evento(client: AsyncClient, api_key_headers: dict[str, str]):
    create = await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "bonanza"},
    )
    item_id = create.json()["id"]

    response = await client.patch(
        f"{API}/eventos/{item_id}",
        headers=api_key_headers,
        json={"status": "em_atendimento"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "em_atendimento"
    assert response.json()["tipo"] == "indicacao_recurso"


# ---------------------------------------------------------------------------
# Permissões — outro portal não pode alterar
# ---------------------------------------------------------------------------


async def test_update_evento_forbidden(
    client: AsyncClient,
    api_key_headers: dict[str, str],
    other_api_key_headers: dict[str, str],
):
    create = await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "bonanza"},
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"{API}/eventos/{item_id}",
        headers=other_api_key_headers,
        json={"status": "atendido"},
    )
    assert response.status_code == 403


async def test_patch_evento_forbidden(
    client: AsyncClient,
    api_key_headers: dict[str, str],
    other_api_key_headers: dict[str, str],
):
    create = await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "bonanza"},
    )
    item_id = create.json()["id"]

    response = await client.patch(
        f"{API}/eventos/{item_id}",
        headers=other_api_key_headers,
        json={"status": "atendido"},
    )
    assert response.status_code == 403


async def test_update_evento_not_found(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    response = await client.put(
        f"{API}/eventos/inexistente",
        headers=api_key_headers,
        json={"status": "atendido"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------


async def test_filter_eventos_by_destinatario(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "bonanza"},
    )
    await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "prefeitura"},
    )

    response = await client.get(
        f"{API}/eventos",
        headers=api_key_headers,
        params={"destinatario": "bonanza"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["destinatario"] == "bonanza"


async def test_filter_eventos_by_status(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    create = await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "bonanza"},
    )
    item_id = create.json()["id"]
    await client.patch(
        f"{API}/eventos/{item_id}",
        headers=api_key_headers,
        json={"status": "atendido"},
    )
    await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "bonanza"},
    )

    response = await client.get(
        f"{API}/eventos",
        headers=api_key_headers,
        params={"status": "aberto"},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1


async def test_filter_eventos_by_tipo(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "indicacao_recurso", "destinatario": "bonanza"},
    )
    await client.post(
        f"{API}/eventos",
        headers=api_key_headers,
        json={"tipo": "outro_tipo", "destinatario": "bonanza"},
    )

    response = await client.get(
        f"{API}/eventos",
        headers=api_key_headers,
        params={"tipo": "indicacao_recurso"},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1
