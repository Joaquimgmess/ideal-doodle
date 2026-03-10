"""Normalizer para portal 05-sos-minas-growberry."""

from app.schemas.normalized import NormalizedResult, Pedido, PontoAjuda, Voluntario
from app.scrapers.base import ScraperResult

from .helpers import base_fields, city_slug, first, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for item in r.data.get("pedidos", []):
        raw_id = first(item, "id", "ID", "codigo") or ""
        city = city_slug(item, "cidade", fallback="mg")
        lat, lng = geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                titulo=first(item, "titulo", "title", "descricao"),
                descricao=first(item, "descricao", "description", "detalhe"),
                categoria=first(item, "categoria", "tipo"),
                status=item.get("status"),
                contato=first(item, "telefone", "phone", "contato", "whatsapp"),
                cidade=item.get("cidade"),
                bairro=first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("voluntarios", []):
        raw_id = first(item, "id", "ID") or ""
        city = city_slug(item, "cidade", fallback="mg")
        lat, lng = geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                nome=first(item, "nome", "name"),
                descricao=first(item, "descricao", "description", "habilidades"),
                categoria=item.get("categoria") or item.get("area"),
                contato=first(item, "telefone", "phone", "contato", "whatsapp"),
                cidade=item.get("cidade"),
                bairro=first(item, "bairro", "neighborhood", "logradouro"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("doacoes", [])):
        raw_id = first(item, "id", "ID") or str(i)
        city = city_slug(item, "cidade", fallback="mg")
        lat, lng = geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                tipo="doacao",
                nome=first(item, "nome", "name", "titulo"),
                endereco=first(item, "endereco", "address"),
                cidade=item.get("cidade"),
                bairro=first(item, "bairro", "neighborhood"),
                contato=first(item, "telefone", "phone", "contato"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr
