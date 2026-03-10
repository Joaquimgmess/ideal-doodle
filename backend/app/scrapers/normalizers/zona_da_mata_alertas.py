"""Normalizer para portal 19-zona-da-mata-alertas."""

from app.schemas.normalized import FeedItem, NormalizedResult
from app.scrapers.base import ScraperResult

from .helpers import base_fields, first


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for i, item in enumerate(r.data.get("alerts", [])):
        raw_id = item.get("id") or str(i)
        alert_type = item.get("type") or ""
        nr.feed.append(
            FeedItem(
                id=f"{pid}:zona_da_mata:{raw_id}",
                **base,
                tipo="alerta",
                titulo=alert_type or "alerta",
                descricao=first(item, "description", "descricao", "message"),
                data=str(item.get("created_at") or ""),
                raw=item,
            )
        )

    return nr
