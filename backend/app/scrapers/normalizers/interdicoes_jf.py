"""Normalizer para portal 16-interdicoes-jf."""

from app.schemas.normalized import FeedItem, NormalizedResult
from app.scrapers.base import ScraperResult

from .helpers import base_fields, md5_short


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for item in r.data.get("interdicoes", []):
        key = f"{item.get('Endereco', '')}:{item.get('Data_Registro', '')}:{item.get('Hora_registro', '')}"
        raw_id = md5_short(key)
        status = item.get("Status", "")
        endereco = item.get("Endereco") or ""
        zona = item.get("Zona") or ""
        titulo = f"{endereco} ({zona})" if zona else endereco
        nr.feed.append(
            FeedItem(
                id=f"{pid}:jf:interdicao:{raw_id}",
                **base,
                tipo="interdicao",
                titulo=titulo or None,
                descricao=item.get("Descricao"),
                data=item.get("Data_Registro") or "",
                urgente=status == "INTERDITADA",
                raw=item,
            )
        )

    return nr
