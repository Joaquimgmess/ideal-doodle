"""Normalizer para portal 15-onde-doar."""

from app.schemas.normalized import NormalizedResult, Pedido, PontoAjuda
from app.scrapers.base import ScraperResult

from .helpers import base_fields, first, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for i, item in enumerate(r.data.get("donation_points", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        # Extrair categorias do array de objetos aninhados
        cats = item.get("categorias") or []
        itens = [
            c["categoria"]["nome"]
            for c in cats
            if isinstance(c, dict) and isinstance(c.get("categoria"), dict)
        ]
        _ender_parts = [p for p in [item.get("endereco"), item.get("numero")] if p]
        endereco = ", ".join(_ender_parts) or None
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:{raw_id}",
                **base,
                tipo="doacao",
                nome=item.get("nome"),
                descricao=item.get("detalhes"),
                endereco=endereco,
                cidade=item.get("cidade") or "Juiz de Fora",
                contato=item.get("telefone") or item.get("whatsapp"),
                itens=itens,
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("help_requests", [])):
        raw_id = first(item, "id", "ID") or str(i)
        lat, lng = geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:jf:pedido:{raw_id}",
                **base,
                titulo=first(item, "titulo", "title"),
                descricao=first(item, "descricao", "description"),
                categoria=first(item, "categoria", "tipo"),
                status=item.get("status"),
                nome=first(item, "nome", "name"),
                contato=first(item, "telefone", "phone", "contato"),
                cidade=first(item, "cidade", "city") or "Juiz de Fora",
                bairro=first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr
