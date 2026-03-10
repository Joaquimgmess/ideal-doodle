"""Normalizer para portal 10-ajude-juiz-de-fora."""

from app.schemas.normalized import FeedItem, NormalizedResult, Pedido, PontoAjuda
from app.scrapers.base import ScraperResult

from .helpers import base_fields, first, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for i, item in enumerate(r.data.get("collection_points", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        itens_raw = item.get("items") or item.get("itens") or []
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:{raw_id}",
                **base,
                tipo="coleta",
                nome=first(item, "name", "nome"),
                endereco=first(item, "address", "endereco"),
                cidade=first(item, "city", "cidade") or "Juiz de Fora",
                bairro=first(item, "neighborhood", "bairro"),
                contato=first(item, "phone", "telefone", "contato"),
                horario=first(item, "hours", "horario"),
                itens=itens_raw if isinstance(itens_raw, list) else [str(itens_raw)],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("needs", [])):
        raw_id = item.get("id") or str(i)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:jf:{raw_id}",
                **base,
                titulo=first(item, "category", "custom_label"),
                descricao=first(item, "custom_label", "category"),
                categoria=item.get("category"),
                status="ativo" if item.get("is_active") else "inativo",
                cidade="Juiz de Fora",
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("reports", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        nr.feed.append(
            FeedItem(
                id=f"{pid}:jf:report:{raw_id}",
                **base,
                tipo="relatorio",
                titulo=first(item, "type", "address"),
                descricao=first(item, "description", "reference"),
                data=str(item.get("created_at") or ""),
                raw=item,
            )
        )

    return nr
