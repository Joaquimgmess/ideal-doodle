"""Normalizer para portal 12-ajuda-imediata."""

from app.schemas.normalized import NormalizedResult, Pedido, Voluntario
from app.scrapers.base import ScraperResult

from .helpers import base_fields, first


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for item in r.data.get("items", []):
        raw_id = item.get("id") or ""
        tipo_pub = item.get("tipo_publicacao", "")
        u = item.get("usuario") or {}
        nome = u.get("nome") or first(item, "nome", "name")
        contato = u.get("telefone") or first(item, "telefone", "whatsapp")
        bairro = u.get("bairro") or item.get("bairro")

        if tipo_pub == "PEDIDO":
            nr.pedidos.append(
                Pedido(
                    id=f"{pid}:jf:{raw_id}",
                    **base,
                    titulo=item.get("descricao") or item.get("categoria"),
                    descricao=item.get("descricao"),
                    categoria=item.get("categoria"),
                    status=item.get("status"),
                    nome=nome,
                    contato=contato,
                    cidade="Juiz de Fora",
                    bairro=bairro,
                    raw=item,
                )
            )
        elif tipo_pub == "OFERTA":
            nr.voluntarios.append(
                Voluntario(
                    id=f"{pid}:jf:{raw_id}",
                    **base,
                    nome=nome,
                    descricao=item.get("descricao"),
                    categoria=item.get("categoria"),
                    contato=contato,
                    cidade="Juiz de Fora",
                    bairro=bairro,
                    raw=item,
                )
            )

    return nr
