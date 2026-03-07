import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import col, func, select

from app.api.deps import ApiKeyDep, SessionDep
from app.models import (
    FeedItem,
    FeedItemCreate,
    FeedItemUpdate,
    Outro,
    OutroCreate,
    OutroUpdate,
    Pedido,
    PedidoCreate,
    PedidoUpdate,
    Pet,
    PetCreate,
    PetUpdate,
    PontoAjuda,
    PontoAjudaCreate,
    PontoAjudaUpdate,
    Voluntario,
    VoluntarioCreate,
    VoluntarioUpdate,
)

router = APIRouter(tags=["data"])

_USER_PORTAL_ID = "usuario"
_USER_PORTAL_NAME = "Contribuição de usuário"
_USER_PORTAL_URL = ""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _user_id(prefix: str, cidade: str | None = None) -> str:
    return f"{_USER_PORTAL_ID}:{cidade or 'sem-cidade'}:{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _list_response(data: list[Any], count: int) -> dict[str, Any]:
    return {"data": data, "count": count}


# ---------------------------------------------------------------------------
# Pedidos
# ---------------------------------------------------------------------------


@router.get("/pedidos")
async def list_pedidos(
    session: SessionDep,
    api_key: ApiKeyDep,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    portal_id: str | None = None,
    cidade: str | None = None,
    categoria: str | None = None,
    status: str | None = None,
) -> Any:
    q = select(Pedido)
    if portal_id:
        q = q.where(Pedido.portal_id == portal_id)
    if cidade:
        q = q.where(Pedido.cidade.ilike(f"%{cidade}%"))  # type: ignore[union-attr]
    if categoria:
        q = q.where(Pedido.categoria.ilike(f"%{categoria}%"))  # type: ignore[union-attr]
    if status:
        q = q.where(Pedido.status == status)

    count = (await session.exec(select(func.count()).select_from(q.subquery()))).one()
    items = (
        await session.exec(
            q.order_by(col(Pedido.scraped_at).desc()).offset(skip).limit(limit)
        )
    ).all()
    return _list_response(items, count)


@router.post("/pedidos", status_code=201)
async def create_pedido(
    session: SessionDep, api_key: ApiKeyDep, data: PedidoCreate
) -> Any:
    item = Pedido(
        id=_user_id("pedido", data.cidade),
        portal_id=_USER_PORTAL_ID,
        portal_name=_USER_PORTAL_NAME,
        portal_url=_USER_PORTAL_URL,
        scraped_at=_now(),
        **data.model_dump(),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put("/pedidos/{item_id}")
async def update_pedido(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: PedidoUpdate
) -> Any:
    item = await session.get(Pedido, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    item.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Voluntários
# ---------------------------------------------------------------------------


@router.get("/voluntarios")
async def list_voluntarios(
    session: SessionDep,
    api_key: ApiKeyDep,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    portal_id: str | None = None,
    cidade: str | None = None,
    categoria: str | None = None,
) -> Any:
    q = select(Voluntario)
    if portal_id:
        q = q.where(Voluntario.portal_id == portal_id)
    if cidade:
        q = q.where(Voluntario.cidade.ilike(f"%{cidade}%"))  # type: ignore[union-attr]
    if categoria:
        q = q.where(Voluntario.categoria.ilike(f"%{categoria}%"))  # type: ignore[union-attr]

    count = (await session.exec(select(func.count()).select_from(q.subquery()))).one()
    items = (
        await session.exec(
            q.order_by(col(Voluntario.scraped_at).desc()).offset(skip).limit(limit)
        )
    ).all()
    return _list_response(items, count)


@router.post("/voluntarios", status_code=201)
async def create_voluntario(
    session: SessionDep, api_key: ApiKeyDep, data: VoluntarioCreate
) -> Any:
    item = Voluntario(
        id=_user_id("voluntario", data.cidade),
        portal_id=_USER_PORTAL_ID,
        portal_name=_USER_PORTAL_NAME,
        portal_url=_USER_PORTAL_URL,
        scraped_at=_now(),
        **data.model_dump(),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put("/voluntarios/{item_id}")
async def update_voluntario(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: VoluntarioUpdate
) -> Any:
    item = await session.get(Voluntario, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado")
    item.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Pontos de Ajuda
# ---------------------------------------------------------------------------


@router.get("/pontos")
async def list_pontos(
    session: SessionDep,
    api_key: ApiKeyDep,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    portal_id: str | None = None,
    cidade: str | None = None,
    tipo: str | None = None,
) -> Any:
    q = select(PontoAjuda)
    if portal_id:
        q = q.where(PontoAjuda.portal_id == portal_id)
    if cidade:
        q = q.where(PontoAjuda.cidade.ilike(f"%{cidade}%"))  # type: ignore[union-attr]
    if tipo:
        q = q.where(PontoAjuda.tipo == tipo)

    count = (await session.exec(select(func.count()).select_from(q.subquery()))).one()
    items = (
        await session.exec(
            q.order_by(col(PontoAjuda.scraped_at).desc()).offset(skip).limit(limit)
        )
    ).all()
    return _list_response(items, count)


@router.post("/pontos", status_code=201)
async def create_ponto(
    session: SessionDep, api_key: ApiKeyDep, data: PontoAjudaCreate
) -> Any:
    item = PontoAjuda(
        id=_user_id("ponto", data.cidade),
        portal_id=_USER_PORTAL_ID,
        portal_name=_USER_PORTAL_NAME,
        portal_url=_USER_PORTAL_URL,
        scraped_at=_now(),
        **data.model_dump(),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put("/pontos/{item_id}")
async def update_ponto(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: PontoAjudaUpdate
) -> Any:
    item = await session.get(PontoAjuda, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ponto de ajuda não encontrado")
    item.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------


@router.get("/pets")
async def list_pets(
    session: SessionDep,
    api_key: ApiKeyDep,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    portal_id: str | None = None,
    cidade: str | None = None,
    tipo: str | None = None,
    especie: str | None = None,
) -> Any:
    q = select(Pet)
    if portal_id:
        q = q.where(Pet.portal_id == portal_id)
    if cidade:
        q = q.where(Pet.cidade.ilike(f"%{cidade}%"))  # type: ignore[union-attr]
    if tipo:
        q = q.where(Pet.tipo == tipo)
    if especie:
        q = q.where(Pet.especie.ilike(f"%{especie}%"))  # type: ignore[union-attr]

    count = (await session.exec(select(func.count()).select_from(q.subquery()))).one()
    items = (
        await session.exec(
            q.order_by(col(Pet.scraped_at).desc()).offset(skip).limit(limit)
        )
    ).all()
    return _list_response(items, count)


@router.post("/pets", status_code=201)
async def create_pet(session: SessionDep, api_key: ApiKeyDep, data: PetCreate) -> Any:
    item = Pet(
        id=_user_id("pet", data.cidade),
        portal_id=_USER_PORTAL_ID,
        portal_name=_USER_PORTAL_NAME,
        portal_url=_USER_PORTAL_URL,
        scraped_at=_now(),
        **data.model_dump(),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put("/pets/{item_id}")
async def update_pet(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: PetUpdate
) -> Any:
    item = await session.get(Pet, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pet não encontrado")
    item.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------


@router.get("/feed")
async def list_feed(
    session: SessionDep,
    api_key: ApiKeyDep,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    portal_id: str | None = None,
    tipo: str | None = None,
    urgente: bool | None = None,
) -> Any:
    q = select(FeedItem)
    if portal_id:
        q = q.where(FeedItem.portal_id == portal_id)
    if tipo:
        q = q.where(FeedItem.tipo == tipo)
    if urgente is not None:
        q = q.where(FeedItem.urgente == urgente)

    count = (await session.exec(select(func.count()).select_from(q.subquery()))).one()
    items = (
        await session.exec(
            q.order_by(col(FeedItem.scraped_at).desc()).offset(skip).limit(limit)
        )
    ).all()
    return _list_response(items, count)


@router.post("/feed", status_code=201)
async def create_feed_item(
    session: SessionDep, api_key: ApiKeyDep, data: FeedItemCreate
) -> Any:
    item = FeedItem(
        id=_user_id("feed"),
        portal_id=_USER_PORTAL_ID,
        portal_name=_USER_PORTAL_NAME,
        portal_url=_USER_PORTAL_URL,
        scraped_at=_now(),
        **data.model_dump(),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put("/feed/{item_id}")
async def update_feed_item(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: FeedItemUpdate
) -> Any:
    item = await session.get(FeedItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de feed não encontrado")
    item.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Outros
# ---------------------------------------------------------------------------


@router.get("/outros")
async def list_outros(
    session: SessionDep,
    api_key: ApiKeyDep,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    portal_id: str | None = None,
    tipo: str | None = None,
) -> Any:
    q = select(Outro)
    if portal_id:
        q = q.where(Outro.portal_id == portal_id)
    if tipo:
        q = q.where(Outro.tipo == tipo)

    count = (await session.exec(select(func.count()).select_from(q.subquery()))).one()
    items = (
        await session.exec(
            q.order_by(col(Outro.scraped_at).desc()).offset(skip).limit(limit)
        )
    ).all()
    return _list_response(items, count)


@router.post("/outros", status_code=201)
async def create_outro(
    session: SessionDep, api_key: ApiKeyDep, data: OutroCreate
) -> Any:
    item = Outro(
        id=_user_id("outro"),
        portal_id=_USER_PORTAL_ID,
        portal_name=_USER_PORTAL_NAME,
        portal_url=_USER_PORTAL_URL,
        scraped_at=_now(),
        **data.model_dump(),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put("/outros/{item_id}")
async def update_outro(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: OutroUpdate
) -> Any:
    item = await session.get(Outro, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    item.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item
