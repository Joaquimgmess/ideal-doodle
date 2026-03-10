"""Normalizer para portal 03-sos-animais-mg."""

from app.schemas.normalized import NormalizedResult, Pet
from app.scrapers.base import ScraperResult

from .helpers import base_fields, city_slug


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    tipo_map = {
        "lost": "perdido",
        "found": "encontrado",
        "adoption": "adocao",
    }
    for category, tipo in tipo_map.items():
        for item in r.data.get(category, []):
            city = city_slug(item, "city", fallback="mg")
            raw_id = item.get("id", "")
            nr.pets.append(
                Pet(
                    id=f"{pid}:{city}:{raw_id}",
                    **base,
                    tipo=tipo,
                    nome=item.get("pet_name"),
                    especie=item.get("animal_type"),
                    descricao=item.get("description"),
                    status=item.get("status"),
                    contato=item.get("phone"),
                    cidade=item.get("city"),
                    imagem_url=item.get("image_url"),
                    raw=item,
                )
            )

    return nr
