"""Normalizer para portal 17-ajuda-emjf."""

from app.schemas.normalized import NormalizedResult, Outro, PontoAjuda
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
                id=f"{pid}:jf:coleta:{raw_id}",
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

    for i, item in enumerate(r.data.get("shelters", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:abrigo:{raw_id}",
                **base,
                tipo="abrigo",
                nome=first(item, "name", "nome"),
                endereco=first(item, "address", "endereco"),
                cidade=first(item, "city", "cidade") or "Juiz de Fora",
                bairro=first(item, "neighborhood", "bairro"),
                contato=first(item, "phone", "telefone", "contato"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("pix_keys", [])):
        raw_id = item.get("id") or str(i)
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:pix:{raw_id}",
                **base,
                tipo="pix",
                titulo=first(item, "name", "nome"),
                descricao=first(item, "description", "descricao"),
                contato=first(item, "pixKey", "pix_key", "chave_pix"),
                raw=item,
            )
        )

    return nr
