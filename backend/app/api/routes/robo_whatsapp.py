from fastapi import APIRouter, HTTPException, Query
from sqlmodel import col, func, select

from app.api.deps import ApiKeyDep, SessionDep
from app.models import Solicitacao, SolicitacaoCreate, SolicitacaoList

router = APIRouter(tags=["robo-whatsapp"])


@router.post("/robo-whatsapp", status_code=201)
async def create_solicitacao(
    session: SessionDep, api_key: ApiKeyDep, data: SolicitacaoCreate
) -> Solicitacao:
    item = Solicitacao(
        portal_id=api_key.slug,
        portal_name=api_key.name,
        **data.model_dump(),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.get("/robo-whatsapp")
async def list_solicitacoes(
    session: SessionDep,
    _api_key: ApiKeyDep,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    prioridade: str | None = None,
    orgao_responsavel: str | None = None,
    risco_imediato: bool | None = None,
) -> SolicitacaoList:
    q = select(Solicitacao)
    if prioridade:
        q = q.where(Solicitacao.prioridade == prioridade)
    if orgao_responsavel:
        q = q.where(Solicitacao.orgao_responsavel == orgao_responsavel)
    if risco_imediato is not None:
        q = q.where(Solicitacao.risco_imediato == risco_imediato)

    count = (await session.exec(select(func.count()).select_from(q.subquery()))).one()
    items = (
        await session.exec(
            q.order_by(col(Solicitacao.criado_em).desc()).offset(skip).limit(limit)
        )
    ).all()
    return SolicitacaoList(data=items, count=count)


@router.get("/robo-whatsapp/{uid}")
async def get_solicitacao(
    session: SessionDep, _api_key: ApiKeyDep, uid: str
) -> Solicitacao:
    item = await session.get(Solicitacao, uid)
    if not item:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    return item
