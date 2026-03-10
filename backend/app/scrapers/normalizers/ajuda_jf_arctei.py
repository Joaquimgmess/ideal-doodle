"""Normalizer para portal 13-ajuda-jf-arctei."""

from app.schemas.normalized import (
    FeedItem,
    NormalizedResult,
    Pedido,
    PontoAjuda,
    Voluntario,
)
from app.scrapers.base import ScraperResult

from .helpers import base_fields, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for i, item in enumerate(r.data.get("requests", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        needs = item.get("needs") or []
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:jf:{raw_id}",
                **base,
                titulo=item.get("details") or ", ".join(needs) if needs else None,
                descricao=item.get("details"),
                categoria=", ".join(needs) if isinstance(needs, list) else str(needs),
                status=item.get("status"),
                nome=item.get("name"),
                contato=str(item["phone"]) if item.get("phone") else None,
                cidade="Juiz de Fora",
                bairro=item.get("neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("points", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        itens_raw = item.get("items") or []
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:{raw_id}",
                **base,
                tipo="coleta",
                nome=item.get("name"),
                endereco=item.get("address"),
                cidade="Juiz de Fora",
                bairro=item.get("neighborhood"),
                contato=str(item.get("contact") or item.get("phone") or "") or None,
                horario=item.get("hours"),
                itens=itens_raw if isinstance(itens_raw, list) else [str(itens_raw)],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("volunteers", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        skills = item.get("skills") or []
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:jf:{raw_id}",
                **base,
                nome=item.get("name"),
                descricao=item.get("notes"),
                categoria=", ".join(skills)
                if isinstance(skills, list)
                else str(skills),
                contato=str(item["phone"]) if item.get("phone") else None,
                cidade="Juiz de Fora",
                bairro=item.get("neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("vistorias", [])):
        raw_id = item.get("id") or str(i)
        nr.feed.append(
            FeedItem(
                id=f"{pid}:jf:vistoria:{raw_id}",
                **base,
                tipo="vistoria",
                titulo=item.get("address") or item.get("neighborhood"),
                descricao=item.get("description"),
                data=str(item.get("created_at") or ""),
                urgente=str(item.get("urgency") or "").lower() == "alta",
                raw=item,
            )
        )

    return nr
