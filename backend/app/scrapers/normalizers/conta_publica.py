"""Normalizer para portal 22-conta-publica."""

from app.schemas.normalized import FeedItem, NormalizedResult, Outro
from app.scrapers.base import ScraperResult

from .helpers import base_fields, first


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    saldo = r.data.get("saldo")
    if saldo and isinstance(saldo, dict):
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:saldo",
                **base,
                tipo="saldo",
                titulo="Saldo Conta Pública",
                descricao=str(
                    saldo.get("saldo")
                    or saldo.get("valor")
                    or saldo.get("saldoTotal")
                    or saldo.get("totalArrecadado")
                    or ""
                ),
                raw=saldo,
            )
        )

    for i, item in enumerate(r.data.get("extrato", [])):
        raw_id = item.get("id") or str(i)
        nr.feed.append(
            FeedItem(
                id=f"{pid}:jf:extrato:{raw_id}",
                **base,
                tipo="transacao",
                titulo=first(item, "descricao", "description", "tipo"),
                descricao=first(item, "detalhe", "detalhes", "observacao"),
                data=str(first(item, "data", "date", "created_at") or ""),
                raw=item,
            )
        )

    registro = r.data.get("registro")
    if registro and isinstance(registro, dict):
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:registro",
                **base,
                tipo="registro",
                titulo="Registro Conta Pública",
                descricao=str(first(registro, "descricao", "description") or ""),
                raw=registro,
            )
        )

    return nr
