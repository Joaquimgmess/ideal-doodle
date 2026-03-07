import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.anyio

API = settings.API_V1_STR


# ---------------------------------------------------------------------------
# Pedidos
# ---------------------------------------------------------------------------


async def test_list_pedidos(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/pedidos", headers=api_key_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] == 0


async def test_create_pedido(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.post(
        f"{API}/pedidos",
        headers=api_key_headers,
        json={"titulo": "Preciso de água", "categoria": "resgate", "cidade": "JF"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Preciso de água"
    assert data["categoria"] == "resgate"
    assert data["cidade"] == "JF"
    assert data["portal_id"] == "test-key"


async def test_update_pedido(client: AsyncClient, api_key_headers: dict[str, str]):
    create = await client.post(
        f"{API}/pedidos",
        headers=api_key_headers,
        json={"titulo": "Original", "cidade": "JF"},
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"{API}/pedidos/{item_id}",
        headers=api_key_headers,
        json={"titulo": "Atualizado"},
    )
    assert response.status_code == 200
    assert response.json()["titulo"] == "Atualizado"


async def test_patch_pedido(client: AsyncClient, api_key_headers: dict[str, str]):
    create = await client.post(
        f"{API}/pedidos",
        headers=api_key_headers,
        json={"titulo": "Original", "cidade": "JF"},
    )
    item_id = create.json()["id"]

    response = await client.patch(
        f"{API}/pedidos/{item_id}",
        headers=api_key_headers,
        json={"status": "em_atendimento"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "em_atendimento"
    assert response.json()["titulo"] == "Original"


async def test_update_pedido_not_found(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    response = await client.put(
        f"{API}/pedidos/inexistente",
        headers=api_key_headers,
        json={"titulo": "X"},
    )
    assert response.status_code == 404


async def test_update_pedido_forbidden(
    client: AsyncClient,
    api_key_headers: dict[str, str],
    other_api_key_headers: dict[str, str],
):
    create = await client.post(
        f"{API}/pedidos",
        headers=api_key_headers,
        json={"titulo": "Meu pedido", "cidade": "JF"},
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"{API}/pedidos/{item_id}",
        headers=other_api_key_headers,
        json={"titulo": "Hackeado"},
    )
    assert response.status_code == 403


async def test_patch_pedido_forbidden(
    client: AsyncClient,
    api_key_headers: dict[str, str],
    other_api_key_headers: dict[str, str],
):
    create = await client.post(
        f"{API}/pedidos",
        headers=api_key_headers,
        json={"titulo": "Meu pedido", "cidade": "JF"},
    )
    item_id = create.json()["id"]

    response = await client.patch(
        f"{API}/pedidos/{item_id}",
        headers=other_api_key_headers,
        json={"status": "atendido"},
    )
    assert response.status_code == 403


async def test_create_pedido_saves_portal_id(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    response = await client.post(
        f"{API}/pedidos",
        headers=api_key_headers,
        json={"titulo": "Teste portal", "cidade": "JF"},
    )
    assert response.status_code == 201
    assert response.json()["portal_id"] == "test-key"


async def test_list_pedidos_no_api_key(client: AsyncClient):
    response = await client.get(f"{API}/pedidos")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Voluntarios
# ---------------------------------------------------------------------------


async def test_list_voluntarios(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/voluntarios", headers=api_key_headers)
    assert response.status_code == 200
    assert response.json()["count"] == 0


async def test_create_voluntario(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.post(
        f"{API}/voluntarios",
        headers=api_key_headers,
        json={"nome": "João", "categoria": "logistica", "cidade": "JF"},
    )
    assert response.status_code == 201
    assert response.json()["nome"] == "João"


async def test_update_voluntario(client: AsyncClient, api_key_headers: dict[str, str]):
    create = await client.post(
        f"{API}/voluntarios",
        headers=api_key_headers,
        json={"nome": "Original", "cidade": "JF"},
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"{API}/voluntarios/{item_id}",
        headers=api_key_headers,
        json={"nome": "Atualizado"},
    )
    assert response.status_code == 200
    assert response.json()["nome"] == "Atualizado"


# ---------------------------------------------------------------------------
# Pontos de Ajuda
# ---------------------------------------------------------------------------


async def test_list_pontos(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/pontos", headers=api_key_headers)
    assert response.status_code == 200
    assert response.json()["count"] == 0


async def test_create_ponto(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.post(
        f"{API}/pontos",
        headers=api_key_headers,
        json={"tipo": "abrigo", "nome": "Abrigo Central", "cidade": "JF"},
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == "abrigo"


async def test_update_ponto(client: AsyncClient, api_key_headers: dict[str, str]):
    create = await client.post(
        f"{API}/pontos",
        headers=api_key_headers,
        json={"tipo": "abrigo", "nome": "Original", "cidade": "JF"},
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"{API}/pontos/{item_id}",
        headers=api_key_headers,
        json={"nome": "Atualizado"},
    )
    assert response.status_code == 200
    assert response.json()["nome"] == "Atualizado"


# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------


async def test_list_pets(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/pets", headers=api_key_headers)
    assert response.status_code == 200
    assert response.json()["count"] == 0


async def test_create_pet(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.post(
        f"{API}/pets",
        headers=api_key_headers,
        json={
            "tipo": "perdido",
            "nome": "Rex",
            "especie": "cachorro",
            "cidade": "JF",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tipo"] == "perdido"
    assert data["nome"] == "Rex"


async def test_update_pet(client: AsyncClient, api_key_headers: dict[str, str]):
    create = await client.post(
        f"{API}/pets",
        headers=api_key_headers,
        json={"tipo": "perdido", "nome": "Rex", "especie": "cachorro", "cidade": "JF"},
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"{API}/pets/{item_id}",
        headers=api_key_headers,
        json={"nome": "Rex Atualizado"},
    )
    assert response.status_code == 200
    assert response.json()["nome"] == "Rex Atualizado"


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------


async def test_list_feed(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/feed", headers=api_key_headers)
    assert response.status_code == 200
    assert response.json()["count"] == 0


async def test_create_feed_item(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.post(
        f"{API}/feed",
        headers=api_key_headers,
        json={"tipo": "alerta", "titulo": "Risco de enchente", "urgente": True},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tipo"] == "alerta"
    assert data["urgente"] is True


async def test_update_feed_item(client: AsyncClient, api_key_headers: dict[str, str]):
    create = await client.post(
        f"{API}/feed",
        headers=api_key_headers,
        json={"tipo": "alerta", "titulo": "Original"},
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"{API}/feed/{item_id}",
        headers=api_key_headers,
        json={"titulo": "Atualizado"},
    )
    assert response.status_code == 200
    assert response.json()["titulo"] == "Atualizado"


# ---------------------------------------------------------------------------
# Outros
# ---------------------------------------------------------------------------


async def test_list_outros(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.get(f"{API}/outros", headers=api_key_headers)
    assert response.status_code == 200
    assert response.json()["count"] == 0


async def test_create_outro(client: AsyncClient, api_key_headers: dict[str, str]):
    response = await client.post(
        f"{API}/outros",
        headers=api_key_headers,
        json={"tipo": "pix", "titulo": "Chave pix doação"},
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == "pix"


async def test_update_outro(client: AsyncClient, api_key_headers: dict[str, str]):
    create = await client.post(
        f"{API}/outros",
        headers=api_key_headers,
        json={"tipo": "pix", "titulo": "Original"},
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"{API}/outros/{item_id}",
        headers=api_key_headers,
        json={"titulo": "Atualizado"},
    )
    assert response.status_code == 200
    assert response.json()["titulo"] == "Atualizado"


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------


async def test_filter_pedidos_by_cidade(
    client: AsyncClient, api_key_headers: dict[str, str]
):
    await client.post(
        f"{API}/pedidos",
        headers=api_key_headers,
        json={"titulo": "A", "cidade": "Juiz de Fora"},
    )
    await client.post(
        f"{API}/pedidos",
        headers=api_key_headers,
        json={"titulo": "B", "cidade": "Ubá"},
    )

    response = await client.get(
        f"{API}/pedidos", headers=api_key_headers, params={"cidade": "Juiz"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["cidade"] == "Juiz de Fora"


async def test_pagination(client: AsyncClient, api_key_headers: dict[str, str]):
    for i in range(5):
        await client.post(
            f"{API}/pedidos",
            headers=api_key_headers,
            json={"titulo": f"Pedido {i}", "cidade": "JF"},
        )

    response = await client.get(
        f"{API}/pedidos", headers=api_key_headers, params={"skip": 0, "limit": 2}
    )
    data = response.json()
    assert data["count"] == 5
    assert len(data["data"]) == 2
