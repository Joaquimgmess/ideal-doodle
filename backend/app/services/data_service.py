"""CRUD genérico para entidades scraped."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlmodel import SQLModel, col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import ApiKey

_USER_PORTAL_URL = ""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _user_id(portal_id: str, cidade: str | None = None) -> str:
    return f"{portal_id}:{cidade or 'sem-cidade'}:{uuid.uuid4().hex[:12]}"


async def list_items(
    session: AsyncSession,
    model: type[SQLModel],
    *,
    filters: list | None = None,
    order_col: InstrumentedAttribute | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list, int]:
    """Lista items com filtros, paginação e contagem."""
    q = select(model)
    for f in filters or []:
        q = q.where(f)

    count = (await session.exec(select(func.count()).select_from(q.subquery()))).one()

    if order_col is not None:
        q = q.order_by(col(order_col).desc())

    items = (await session.exec(q.offset(skip).limit(limit))).all()
    return items, count


async def create_item(
    session: AsyncSession,
    model: type[SQLModel],
    api_key: ApiKey,
    data: SQLModel,
    *,
    cidade: str | None = None,
) -> SQLModel:
    """Cria item com metadados de portal."""
    fields = {
        "id": _user_id(api_key.slug, cidade),
        "portal_id": api_key.slug,
        "portal_name": getattr(data, "portal_name", None) or api_key.name,
        "portal_url": _USER_PORTAL_URL,
        "scraped_at": _now(),
        **data.model_dump(exclude={"portal_name"}),
    }
    item = model(**fields)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def get_item_or_404(
    session: AsyncSession,
    model: type[SQLModel],
    item_id: str,
    label: str,
) -> SQLModel:
    """Busca item por ID ou levanta 404."""
    item = await session.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"{label} não encontrado")
    return item


def check_ownership(item: SQLModel, api_key: ApiKey) -> None:
    """Verifica se o caller é dono do item."""
    if item.portal_id != api_key.slug:  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=403, detail="Sem permissão para alterar este registro"
        )


def check_ownership_or_destinatario(item: SQLModel, api_key: ApiKey) -> None:
    """Verifica se o caller é remetente ou destinatário (para Eventos)."""
    portal_id = item.portal_id  # type: ignore[attr-defined]
    destinatario = item.destinatario  # type: ignore[attr-defined]
    if api_key.slug not in (portal_id, destinatario):
        raise HTTPException(
            status_code=403, detail="Sem permissão para alterar este registro"
        )


async def update_item(
    session: AsyncSession,
    item: SQLModel,
    data: SQLModel,
) -> SQLModel:
    """Aplica update (PUT ou PATCH) e persiste."""
    item.sqlmodel_update(data.model_dump(exclude_unset=True))  # type: ignore[attr-defined]
    item.updated_at = _now()  # type: ignore[attr-defined]
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item
