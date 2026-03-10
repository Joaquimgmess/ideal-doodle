"""Normalizer para portal 06-sosjf-org."""

from app.schemas.normalized import FeedItem, NormalizedResult
from app.scrapers.base import ScraperResult

from .helpers import base_fields, first


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    tipo_map = {
        "alerts": "alerta",
        "news": "noticia",
        "reports": "relatorio",
    }
    for category, tipo in tipo_map.items():
        for item in r.data.get(category, []):
            raw_id = item.get("id", "")
            nr.feed.append(
                FeedItem(
                    id=f"{pid}:jf:{raw_id}",
                    **base,
                    tipo=tipo,
                    titulo=first(item, "titulo", "title", "name"),
                    descricao=first(
                        item, "descricao", "description", "content", "body"
                    ),
                    url=first(item, "url", "link", "href"),
                    data=str(item["date"]) if item.get("date") else None,
                    urgente=bool(item.get("urgente") or item.get("urgent")),
                    raw=item,
                )
            )

    return nr
