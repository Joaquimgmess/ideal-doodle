from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import ApiKeyDep, SessionDep
from app.models import KPIHistory

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("/")
async def listar_kpis(session: SessionDep, _api_key: ApiKeyDep) -> list[KPIHistory]:
    """Retorna todos os registros de KPI, do mais recente ao mais antigo."""
    result = await session.execute(
        select(KPIHistory).order_by(KPIHistory.data_registro.desc())
    )
    return result.scalars().all()


@router.get("/ultimo")
async def ultimo_kpi(
    session: SessionDep, _api_key: ApiKeyDep, nome: str = "total_voluntarios"
) -> KPIHistory | None:
    """Retorna o valor mais recente de um KPI pelo nome."""
    result = await session.execute(
        select(KPIHistory)
        .where(KPIHistory.nome_kpi == nome)
        .order_by(KPIHistory.data_registro.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
