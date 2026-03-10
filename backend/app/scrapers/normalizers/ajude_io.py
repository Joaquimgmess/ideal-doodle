"""Normalizer para portal 08-ajude-io."""

from app.schemas.normalized import (
    NormalizedResult,
    Pedido,
    PontoAjuda,
    Voluntario,
)
from app.scrapers.base import ScraperResult

from .helpers import base_fields, city_slug, first, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    def _ajude_geo(item: dict) -> tuple[float | None, float | None]:
        lat, lng = geo(item)
        if lat is None and isinstance(item.get("localizacao"), dict):
            lat, lng = geo(item["localizacao"])
        return lat, lng

    for item in r.data.get("help_requests", []):
        raw_id = item.get("id", "")
        city = city_slug(item, "cidade", "city", fallback="jf")
        lat, lng = _ajude_geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                titulo=first(item, "titulo", "title", "tipo"),
                descricao=first(item, "descricao", "description", "detalhes"),
                categoria=first(item, "categoria", "tipo", "category"),
                status=item.get("status"),
                nome=first(item, "nome", "name", "solicitante"),
                contato=first(item, "telefone", "phone", "contato", "whatsapp"),
                cidade=first(item, "cidade", "city"),
                bairro=first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("volunteer_offers", []):
        raw_id = item.get("id", "")
        city = city_slug(item, "cidade", "city", fallback="jf")
        lat, lng = _ajude_geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                nome=first(item, "nome", "name"),
                descricao=first(item, "descricao", "description", "habilidades"),
                categoria=first(item, "categoria", "tipo", "category"),
                contato=first(item, "telefone", "phone", "contato"),
                cidade=first(item, "cidade", "city"),
                bairro=first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("donation_points", [])):
        raw_id = item.get("id") or str(i)
        city = city_slug(item, "cidade", "city", fallback="jf")
        lat, lng = _ajude_geo(item)
        itens_raw = (
            item.get("itens") or item.get("items") or item.get("necessidades") or []
        )
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                tipo="doacao",
                nome=first(item, "nome", "name"),
                endereco=first(item, "endereco", "address"),
                cidade=first(item, "cidade", "city"),
                bairro=first(item, "bairro", "neighborhood"),
                contato=first(item, "telefone", "phone", "contato"),
                horario=first(item, "horario", "hours"),
                itens=itens_raw if isinstance(itens_raw, list) else [str(itens_raw)],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("shelters", [])):
        raw_id = item.get("id") or item.get("name") or str(i)
        lat, lng = geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:abrigo:{raw_id}",
                **base,
                tipo="abrigo",
                nome=item.get("name") or item.get("nome"),
                bairro=item.get("neighborhood") or item.get("bairro"),
                cidade="Juiz de Fora",
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr
