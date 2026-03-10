"""Normalizer para portal 09-cidade-que-cuida."""

from typing import Any

from app.schemas.normalized import (
    NormalizedResult,
    Pedido,
    PontoAjuda,
    Voluntario,
)
from app.scrapers.base import ScraperResult

from .helpers import base_fields, first, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    def _users(item: dict[str, Any]) -> dict[str, Any]:
        u = item.get("users")
        return u if isinstance(u, dict) else {}

    for item in r.data.get("pedidos", []):
        raw_id = item.get("id", "")
        u = _users(item)
        lat, lng = geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:jf:{raw_id}",
                **base,
                titulo=first(item, "titulo", "title"),
                descricao=first(item, "descricao", "description"),
                categoria=first(item, "categoria", "tipo"),
                status=item.get("status"),
                nome=u.get("nome"),
                contato=u.get("telefone") or first(item, "telefone", "phone"),
                cidade="Juiz de Fora",
                bairro=first(item, "bairro") or u.get("bairro"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("voluntarios", []):
        raw_id = item.get("id", "")
        u = _users(item)
        lat, lng = geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:jf:{raw_id}",
                **base,
                nome=u.get("nome") or first(item, "nome"),
                descricao=first(item, "descricao", "description", "titulo", "title"),
                categoria=first(item, "categoria", "tipo"),
                contato=u.get("telefone") or first(item, "telefone"),
                cidade="Juiz de Fora",
                bairro=first(item, "bairro") or u.get("bairro"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("doacoes", []):
        raw_id = item.get("id", "")
        u = _users(item)
        lat, lng = geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:{raw_id}",
                **base,
                tipo="doacao",
                nome=first(item, "titulo", "title"),
                descricao=first(item, "descricao", "description"),
                cidade="Juiz de Fora",
                bairro=first(item, "bairro") or u.get("bairro"),
                contato=u.get("telefone") or first(item, "telefone"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("entidades", []):
        raw_id = item.get("id", "")
        lat, lng = geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:entidade:{raw_id}",
                **base,
                tipo="entidade",
                nome=first(item, "nome", "name", "titulo"),
                endereco=first(item, "endereco", "address"),
                cidade="Juiz de Fora",
                bairro=first(item, "bairro", "neighborhood"),
                contato=first(item, "telefone", "phone", "contato"),
                horario=first(item, "horario", "horarios"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr
