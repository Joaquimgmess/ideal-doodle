"""Normalizer para portal 07-sosjf-online."""

from app.schemas.normalized import NormalizedResult, PontoAjuda
from app.scrapers.base import ScraperResult

from .helpers import base_fields, first, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    tipo_map = {
        "collection_points": "coleta",
        "shelters": "abrigo",
    }
    for key, tipo in tipo_map.items():
        for i, item in enumerate(r.data.get(key, [])):
            raw_id = first(item, "id", "ID") or str(i)
            bairro = item.get("neighborhood") or item.get("bairro")
            lat, lng = geo(item)
            if lat is None and isinstance(item.get("location"), dict):
                lat, lng = geo(item["location"])
            nr.pontos.append(
                PontoAjuda(
                    id=f"{pid}:jf:{raw_id}",
                    **base,
                    tipo=tipo,
                    nome=first(item, "name", "nome"),
                    endereco=first(item, "address", "endereco"),
                    bairro=bairro,
                    cidade="Juiz de Fora",
                    contato=first(item, "phone", "telefone", "contato"),
                    horario=first(item, "horario", "hours"),
                    itens=item.get("acceptedItems")
                    or item.get("itens")
                    or item.get("items")
                    or [],
                    lat=lat,
                    lng=lng,
                    raw=item,
                )
            )

    return nr
