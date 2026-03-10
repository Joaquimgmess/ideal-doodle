"""Normalizer para portal 11-sos-ser-luz-jf."""

from app.schemas.normalized import NormalizedResult, Outro
from app.scrapers.base import ScraperResult

from .helpers import base_fields


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    form_info = r.data.get("form_fields", {})
    if form_info.get("available"):
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:form_structure",
                **base,
                tipo="formulario",
                titulo="Formulário de Pedido de Ajuda",
                descricao=r.data.get("note", ""),
                url=f"{r.url}/help_requests/new",
                raw=form_info,
            )
        )

    return nr
