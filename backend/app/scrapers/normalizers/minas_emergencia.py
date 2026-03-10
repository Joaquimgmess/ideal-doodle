"""Normalizer para portal 02-minas-emergencia."""

from app.schemas.normalized import NormalizedResult, PontoAjuda
from app.scrapers.base import ScraperResult

from .helpers import base_fields, city_slug, first, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for i, item in enumerate(r.data.get("pontos", [])):
        raw_id = first(item, "id", "ID") or str(i)
        city = city_slug(item, "cidade", fallback="mg")
        lat, lng = geo(item)
        itens_raw = item.get("itens") or []
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                tipo=item.get("tipo") or "ponto",
                nome=item.get("nome"),
                endereco=item.get("endereco"),
                cidade=item.get("cidade"),
                bairro=item.get("bairro"),
                contato=item.get("contato"),
                horario=item.get("horario"),
                itens=itens_raw if isinstance(itens_raw, list) else [],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr
