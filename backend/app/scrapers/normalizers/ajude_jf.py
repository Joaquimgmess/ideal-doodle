"""Normalizer para portal 21-ajude-jf."""

from app.schemas.normalized import (
    NormalizedResult,
    Outro,
    Pet,
    PontoAjuda,
    Voluntario,
)
from app.scrapers.base import ScraperResult

from .helpers import base_fields, city_slug, first, geo


def normalize(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    base = base_fields(r)
    pid = r.portal_id

    # Pets perdidos
    for item in r.data.get("pets_perdidos_public", []):
        raw_id = item.get("id") or ""
        nr.pets.append(
            Pet(
                id=f"{pid}:jf:perdido:{raw_id}",
                **base,
                tipo="perdido",
                nome=item.get("nome_pet"),
                especie=item.get("especie"),
                descricao=first(item, "descricao", "cor"),
                status=item.get("status"),
                bairro=item.get("local_visto"),
                imagem_url=item.get("foto_url"),
                raw=item,
            )
        )

    # Adoção
    for item in r.data.get("adocao", []):
        raw_id = item.get("id") or ""
        nr.pets.append(
            Pet(
                id=f"{pid}:jf:adocao:{raw_id}",
                **base,
                tipo="adocao",
                nome=item.get("nome_pet") or item.get("nome"),
                especie=item.get("especie"),
                descricao=item.get("descricao"),
                status=item.get("status"),
                imagem_url=item.get("foto_url"),
                raw=item,
            )
        )

    # Voluntários
    for item in r.data.get("voluntarios_public", []):
        raw_id = item.get("id") or ""
        habilidades = item.get("habilidades") or []
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:jf:{raw_id}",
                **base,
                descricao=item.get("disponibilidade"),
                categoria=", ".join(habilidades)
                if isinstance(habilidades, list) and habilidades
                else item.get("disponibilidade"),
                cidade="Juiz de Fora",
                raw=item,
            )
        )

    # Lares temporários → voluntário (categoria: lar_temporario)
    for item in r.data.get("lares_temporarios_public", []):
        raw_id = item.get("id") or ""
        city = city_slug(item, "cidade", "city", fallback="jf")
        lat, lng = geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:{city}:lar:{raw_id}",
                **base,
                nome=first(item, "nome", "name"),
                descricao=first(item, "descricao", "description", "observacao"),
                categoria="lar_temporario",
                contato=first(item, "telefone", "phone", "contato", "whatsapp"),
                cidade=first(item, "cidade", "city"),
                bairro=first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    # Doadores → voluntário (categoria: doador)
    for item in r.data.get("doadores_public", []):
        raw_id = item.get("id") or ""
        city = city_slug(item, "cidade", "city", fallback="jf")
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:{city}:doador:{raw_id}",
                **base,
                nome=first(item, "nome", "name"),
                descricao=first(item, "descricao", "description"),
                categoria="doador",
                contato=first(item, "telefone", "phone", "contato"),
                cidade=first(item, "cidade", "city"),
                bairro=first(item, "bairro", "neighborhood"),
                raw=item,
            )
        )

    # ONGs / protetores → ponto (tipo: entidade)
    for item in r.data.get("ongs_protetores", []):
        raw_id = item.get("id") or ""
        lat, lng = geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:ong:{raw_id}",
                **base,
                tipo="entidade",
                nome=first(item, "nome", "name"),
                descricao=first(item, "descricao", "description"),
                endereco=first(item, "endereco", "address"),
                cidade=first(item, "cidade", "city") or "Juiz de Fora",
                bairro=first(item, "bairro", "neighborhood"),
                contato=first(item, "telefone", "phone", "contato"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    # Pontos de doação
    for item in r.data.get("pontos_doacao", []):
        raw_id = item.get("id") or ""
        lat, lng = geo(item)
        itens_raw = item.get("itens") or item.get("items") or []
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:doacao:{raw_id}",
                **base,
                tipo="doacao",
                nome=first(item, "nome", "name"),
                endereco=first(item, "endereco", "address"),
                cidade=first(item, "cidade", "city") or "Juiz de Fora",
                bairro=first(item, "bairro", "neighborhood"),
                contato=first(item, "telefone", "phone", "contato"),
                horario=first(item, "horario", "hours"),
                itens=itens_raw if isinstance(itens_raw, list) else [str(itens_raw)],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    # Pontos de alimentação
    for item in r.data.get("pontos_alimentacao", []):
        raw_id = item.get("id") or ""
        lat, lng = geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:alimentacao:{raw_id}",
                **base,
                tipo="alimentacao",
                nome=first(item, "nome", "name"),
                endereco=first(item, "endereco", "address"),
                cidade=first(item, "cidade", "city") or "Juiz de Fora",
                bairro=first(item, "bairro", "neighborhood"),
                contato=first(item, "telefone", "phone", "contato"),
                horario=first(item, "horario", "hours"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    # Abrigos
    for item in r.data.get("abrigos", []):
        raw_id = item.get("id") or ""
        lat, lng = geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:abrigo:{raw_id}",
                **base,
                tipo="abrigo",
                nome=first(item, "nome", "name"),
                endereco=first(item, "endereco", "address"),
                cidade=first(item, "cidade", "city") or "Juiz de Fora",
                bairro=first(item, "bairro", "neighborhood"),
                contato=first(item, "telefone", "phone", "contato"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    # Vaquinhas → outro
    for item in r.data.get("vaquinhas", []):
        raw_id = item.get("id") or ""
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:vaquinha:{raw_id}",
                **base,
                tipo="vaquinha",
                titulo=first(item, "titulo", "title", "nome"),
                descricao=first(item, "descricao", "description"),
                url=first(item, "url", "link"),
                raw=item,
            )
        )

    return nr
