"""Normalizer para portal 01-emergencia-mg."""

from app.schemas.normalized import NormalizedResult, Outro, PontoAjuda, Voluntario
from app.scrapers.base import ScraperResult

from .helpers import base_fields, geo, md5_short


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for item in r.data.get("emergency_contacts", []):
        raw_id = md5_short(str(item.get("nome", "")) + str(item.get("telefone", "")))
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:contato:{raw_id}",
                **base,
                tipo="contato_emergencia",
                titulo=item.get("nome"),
                contato=item.get("telefone"),
                raw=item,
            )
        )

    for item in r.data.get("help_links", []):
        raw_id = md5_short(str(item.get("titulo", "")) + str(item.get("url", "")))
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:link:{raw_id}",
                **base,
                tipo="link",
                titulo=item.get("titulo"),
                descricao=item.get("descricao"),
                url=item.get("url"),
                raw=item,
            )
        )

    for item in r.data.get("animal_shelters", []):
        raw_id = md5_short(str(item.get("nome", "")))
        lat, lng = geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:abrigo_animal:{raw_id}",
                **base,
                tipo="abrigo_animal",
                nome=item.get("nome"),
                contato=item.get("telefone") or item.get("whatsapp_url"),
                itens=item.get("animais", []),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("transport_volunteers", []):
        raw_id = md5_short(str(item.get("nome", "")) + str(item.get("telefone", "")))
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:jf:transporte:{raw_id}",
                **base,
                nome=item.get("nome"),
                categoria="transporte",
                contato=item.get("telefone") or item.get("whatsapp_url"),
                raw=item,
            )
        )

    return nr
