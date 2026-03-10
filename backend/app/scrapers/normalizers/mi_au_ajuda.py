"""Normalizer para portal 18-mi-au-ajuda."""

from app.schemas.normalized import NormalizedResult, Pet, Voluntario
from app.scrapers.base import ScraperResult

from .helpers import base_fields, city_slug, first, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    for i, item in enumerate(r.data.get("acolhedores", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:jf:{raw_id}",
                **base,
                nome=item.get("nome"),
                descricao=item.get("observacoes"),
                categoria="acolhedor_animal",
                contato=item.get("whatsapp") or item.get("email"),
                cidade="Juiz de Fora",
                bairro=item.get("bairro"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("pets", []):
        raw_id = item.get("id") or ""
        city = city_slug(item, "cidade", "city", fallback="jf")
        nr.pets.append(
            Pet(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                tipo=first(item, "tipo", "type") or "perdido",
                nome=first(item, "nome", "name", "nome_pet"),
                especie=first(item, "especie", "animal_type", "tipo_animal"),
                porte=first(item, "porte", "size"),
                descricao=first(item, "descricao", "description"),
                status=item.get("status"),
                contato=first(item, "telefone", "phone", "contato"),
                cidade=first(item, "cidade", "city"),
                bairro=first(item, "bairro", "neighborhood"),
                imagem_url=first(item, "imagem_url", "image_url", "foto"),
                raw=item,
            )
        )

    return nr
