"""Normalizer para portal 20-unidos-por-jf."""

from app.schemas.normalized import NormalizedResult, Pedido, Voluntario
from app.scrapers.base import ScraperResult

from .helpers import base_fields, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for i, item in enumerate(r.data.get("pedidos", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:jf:{raw_id}",
                **base,
                titulo=item.get("need_type") or item.get("description"),
                descricao=item.get("description"),
                categoria=item.get("need_type"),
                status=item.get("status"),
                nome=item.get("name"),
                contato=item.get("phone"),
                cidade="Juiz de Fora",
                bairro=item.get("neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("voluntarios", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:jf:{raw_id}",
                **base,
                nome=item.get("name"),
                descricao=item.get("description"),
                categoria=item.get("need_type"),
                contato=item.get("phone"),
                cidade="Juiz de Fora",
                bairro=item.get("neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr
