from fastapi import APIRouter, Query
from sqlmodel import SQLModel

from app.api.deps import ApiKeyDep, SessionDep
from app.models import (
    Evento,
    EventoCreate,
    EventoList,
    EventoUpdate,
    FeedItem,
    FeedItemCreate,
    FeedItemList,
    FeedItemUpdate,
    Outro,
    OutroCreate,
    OutroList,
    OutroUpdate,
    Pedido,
    PedidoCreate,
    PedidoList,
    PedidoUpdate,
    Pet,
    PetCreate,
    PetList,
    PetUpdate,
    PontoAjuda,
    PontoAjudaCreate,
    PontoAjudaList,
    PontoAjudaUpdate,
    Voluntario,
    VoluntarioCreate,
    VoluntarioList,
    VoluntarioUpdate,
)
from app.services.data_service import (
    check_ownership,
    check_ownership_or_destinatario,
    create_item,
    get_item_or_404,
    list_items,
    update_item,
)

router = APIRouter(tags=["data"])


# ---------------------------------------------------------------------------
# Helpers de filtro
# ---------------------------------------------------------------------------


def _ilike(field, value: str | None):
    """Retorna filtro ilike se value não for None. Escapa wildcards do input."""
    if value:
        escaped = value.replace("%", r"\%").replace("_", r"\_")
        return field.ilike(f"%{escaped}%")  # type: ignore[union-attr]
    return None


def _eq(field, value):
    """Retorna filtro de igualdade se value não for None."""
    if value is not None:
        return field == value
    return None


def _build_filters(*conditions) -> list:
    """Filtra Nones e retorna lista de condições."""
    return [c for c in conditions if c is not None]


# ---------------------------------------------------------------------------
# Generic update/patch (owner check)
# ---------------------------------------------------------------------------


async def _update(
    session: SessionDep,
    api_key: ApiKeyDep,
    model: type[SQLModel],
    item_id: str,
    data: SQLModel,
    label: str,
) -> SQLModel:
    item = await get_item_or_404(session, model, item_id, label)
    check_ownership(item, api_key)
    return await update_item(session, item, data)


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
) -> PedidoList:
    items, count = await list_items(
        session,
        Pedido,
        filters=_build_filters(
            _eq(Pedido.portal_id, portal_id),
            _ilike(Pedido.cidade, cidade),
            _ilike(Pedido.categoria, categoria),
            _eq(Pedido.status, status),
        ),
        order_col=Pedido.scraped_at,
        skip=skip,
        limit=limit,
    )
    return PedidoList(data=items, count=count)


@router.post("/pedidos", status_code=201)
async def create_pedido(
    session: SessionDep, api_key: ApiKeyDep, data: PedidoCreate
) -> Pedido:
    return await create_item(session, Pedido, api_key, data, cidade=data.cidade)


@router.put("/pedidos/{item_id}")
async def update_pedido(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: PedidoUpdate
) -> Pedido:
    return await _update(session, api_key, Pedido, item_id, data, "Pedido")


@router.patch("/pedidos/{item_id}")
async def patch_pedido(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: PedidoUpdate
) -> Pedido:
    return await _update(session, api_key, Pedido, item_id, data, "Pedido")


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
) -> VoluntarioList:
    items, count = await list_items(
        session,
        Voluntario,
        filters=_build_filters(
            _eq(Voluntario.portal_id, portal_id),
            _ilike(Voluntario.cidade, cidade),
            _ilike(Voluntario.categoria, categoria),
        ),
        order_col=Voluntario.scraped_at,
        skip=skip,
        limit=limit,
    )
    return VoluntarioList(data=items, count=count)


@router.post("/voluntarios", status_code=201)
async def create_voluntario(
    session: SessionDep, api_key: ApiKeyDep, data: VoluntarioCreate
) -> Voluntario:
    return await create_item(session, Voluntario, api_key, data, cidade=data.cidade)


@router.put("/voluntarios/{item_id}")
async def update_voluntario(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: VoluntarioUpdate
) -> Voluntario:
    return await _update(session, api_key, Voluntario, item_id, data, "Voluntário")


@router.patch("/voluntarios/{item_id}")
async def patch_voluntario(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: VoluntarioUpdate
) -> Voluntario:
    return await _update(session, api_key, Voluntario, item_id, data, "Voluntário")


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
) -> PontoAjudaList:
    items, count = await list_items(
        session,
        PontoAjuda,
        filters=_build_filters(
            _eq(PontoAjuda.portal_id, portal_id),
            _ilike(PontoAjuda.cidade, cidade),
            _eq(PontoAjuda.tipo, tipo),
        ),
        order_col=PontoAjuda.scraped_at,
        skip=skip,
        limit=limit,
    )
    return PontoAjudaList(data=items, count=count)


@router.post("/pontos", status_code=201)
async def create_ponto(
    session: SessionDep, api_key: ApiKeyDep, data: PontoAjudaCreate
) -> PontoAjuda:
    return await create_item(session, PontoAjuda, api_key, data, cidade=data.cidade)


@router.put("/pontos/{item_id}")
async def update_ponto(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: PontoAjudaUpdate
) -> PontoAjuda:
    return await _update(session, api_key, PontoAjuda, item_id, data, "Ponto de ajuda")


@router.patch("/pontos/{item_id}")
async def patch_ponto(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: PontoAjudaUpdate
) -> PontoAjuda:
    return await _update(session, api_key, PontoAjuda, item_id, data, "Ponto de ajuda")


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
) -> PetList:
    items, count = await list_items(
        session,
        Pet,
        filters=_build_filters(
            _eq(Pet.portal_id, portal_id),
            _ilike(Pet.cidade, cidade),
            _eq(Pet.tipo, tipo),
            _ilike(Pet.especie, especie),
        ),
        order_col=Pet.scraped_at,
        skip=skip,
        limit=limit,
    )
    return PetList(data=items, count=count)


@router.post("/pets", status_code=201)
async def create_pet(session: SessionDep, api_key: ApiKeyDep, data: PetCreate) -> Pet:
    return await create_item(session, Pet, api_key, data, cidade=data.cidade)


@router.put("/pets/{item_id}")
async def update_pet(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: PetUpdate
) -> Pet:
    return await _update(session, api_key, Pet, item_id, data, "Pet")


@router.patch("/pets/{item_id}")
async def patch_pet(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: PetUpdate
) -> Pet:
    return await _update(session, api_key, Pet, item_id, data, "Pet")


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
) -> FeedItemList:
    items, count = await list_items(
        session,
        FeedItem,
        filters=_build_filters(
            _eq(FeedItem.portal_id, portal_id),
            _eq(FeedItem.tipo, tipo),
            _eq(FeedItem.urgente, urgente),
        ),
        order_col=FeedItem.scraped_at,
        skip=skip,
        limit=limit,
    )
    return FeedItemList(data=items, count=count)


@router.post("/feed", status_code=201)
async def create_feed_item(
    session: SessionDep, api_key: ApiKeyDep, data: FeedItemCreate
) -> FeedItem:
    return await create_item(session, FeedItem, api_key, data)


@router.put("/feed/{item_id}")
async def update_feed_item(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: FeedItemUpdate
) -> FeedItem:
    return await _update(session, api_key, FeedItem, item_id, data, "Item de feed")


@router.patch("/feed/{item_id}")
async def patch_feed_item(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: FeedItemUpdate
) -> FeedItem:
    return await _update(session, api_key, FeedItem, item_id, data, "Item de feed")


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
) -> OutroList:
    items, count = await list_items(
        session,
        Outro,
        filters=_build_filters(
            _eq(Outro.portal_id, portal_id),
            _eq(Outro.tipo, tipo),
        ),
        order_col=Outro.scraped_at,
        skip=skip,
        limit=limit,
    )
    return OutroList(data=items, count=count)


@router.post("/outros", status_code=201)
async def create_outro(
    session: SessionDep, api_key: ApiKeyDep, data: OutroCreate
) -> Outro:
    return await create_item(session, Outro, api_key, data)


@router.put("/outros/{item_id}")
async def update_outro(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: OutroUpdate
) -> Outro:
    return await _update(session, api_key, Outro, item_id, data, "Item")


@router.patch("/outros/{item_id}")
async def patch_outro(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: OutroUpdate
) -> Outro:
    return await _update(session, api_key, Outro, item_id, data, "Item")


# ---------------------------------------------------------------------------
# Eventos (permissão especial: remetente OU destinatário)
# ---------------------------------------------------------------------------


@router.get("/eventos")
async def list_eventos(
    session: SessionDep,
    api_key: ApiKeyDep,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    portal_id: str | None = None,
    destinatario: str | None = None,
    tipo: str | None = None,
    status: str | None = None,
) -> EventoList:
    items, count = await list_items(
        session,
        Evento,
        filters=_build_filters(
            _eq(Evento.portal_id, portal_id),
            _eq(Evento.destinatario, destinatario),
            _eq(Evento.tipo, tipo),
            _eq(Evento.status, status),
        ),
        order_col=Evento.scraped_at,
        skip=skip,
        limit=limit,
    )
    return EventoList(data=items, count=count)


@router.post("/eventos", status_code=201)
async def create_evento(
    session: SessionDep, api_key: ApiKeyDep, data: EventoCreate
) -> Evento:
    return await create_item(session, Evento, api_key, data)


async def _update_evento(
    session: SessionDep,
    api_key: ApiKeyDep,
    item_id: str,
    data: EventoUpdate,
) -> Evento:
    item = await get_item_or_404(session, Evento, item_id, "Evento")
    check_ownership_or_destinatario(item, api_key)
    return await update_item(session, item, data)


@router.put("/eventos/{item_id}")
async def update_evento(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: EventoUpdate
) -> Evento:
    return await _update_evento(session, api_key, item_id, data)


@router.patch("/eventos/{item_id}")
async def patch_evento(
    session: SessionDep, api_key: ApiKeyDep, item_id: str, data: EventoUpdate
) -> Evento:
    return await _update_evento(session, api_key, item_id, data)
