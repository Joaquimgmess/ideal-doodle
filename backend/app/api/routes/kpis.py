from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import ApiKeyDep, SessionDep
from app.models import KPIHistory, KPIHistoryList, KPIHistoryPublic

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("/")
async def listar_kpis(
    session: SessionDep,
    _api_key: ApiKeyDep,
    nome: str | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
) -> KPIHistoryList:
    """Retorna registros de KPI paginados, do mais recente ao mais antigo."""
    q = select(KPIHistory)
    if nome:
        q = q.where(KPIHistory.nome_kpi == nome)

    count = (await session.exec(select(func.count()).select_from(q.subquery()))).one()
    items = (
        await session.exec(
            q.order_by(KPIHistory.data_registro.desc()).offset(skip).limit(limit)
        )
    ).all()
    return KPIHistoryList(data=items, count=count)


@router.get("/ultimo")
async def ultimo_kpi(
    session: SessionDep,
    _api_key: ApiKeyDep,
    nome: str,
) -> KPIHistoryPublic:
    """Retorna o valor mais recente de um KPI pelo nome."""
    kpi = (
        await session.exec(
            select(KPIHistory)
            .where(KPIHistory.nome_kpi == nome)
            .order_by(KPIHistory.data_registro.desc())
            .limit(1)
        )
    ).first()
    if kpi is None:
        raise HTTPException(status_code=404, detail="KPI não encontrado")
    return kpi
