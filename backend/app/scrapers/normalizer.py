"""
Normaliza ScraperResult bruto → NormalizedResult com schema unificado.

IDs seguem o padrão: portal_id:cidade:raw_id
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.schemas.normalized import (
    FeedItem,
    NormalizedResult,
    Outro,
    Pedido,
    Pet,
    PontoAjuda,
    Voluntario,
)
from app.scrapers.base import ScraperResult

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _first(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Retorna o primeiro valor não-nulo/vazio entre as chaves fornecidas."""
    for k in keys:
        v = d.get(k)
        if v is not None and v != "":
            return v
    return default


def _geo(d: dict[str, Any]) -> tuple[float | None, float | None]:
    lat = _first(d, "lat", "latitude", "Latitude")
    lng = _first(d, "lng", "longitude", "lon", "Longitude")
    try:
        return (
            float(lat) if lat is not None else None,
            float(lng) if lng is not None else None,
        )
    except (TypeError, ValueError):
        return None, None


def _city_slug(d: dict[str, Any], *keys: str, fallback: str = "mg") -> str:
    v = _first(d, *keys) or fallback
    return str(v).lower().replace(" ", "_")


# ---------------------------------------------------------------------------
# dispatcher
# ---------------------------------------------------------------------------

_NORMALIZERS: dict[str, Any] = {}


def normalize(result: ScraperResult) -> NormalizedResult:
    fn = _NORMALIZERS.get(result.portal_id)
    if fn is None:
        return NormalizedResult()
    return fn(result)


def normalize_all(results: list[ScraperResult]) -> NormalizedResult:
    combined = NormalizedResult()
    for r in results:
        nr = normalize(r)
        combined.pedidos.extend(nr.pedidos)
        combined.voluntarios.extend(nr.voluntarios)
        combined.pontos.extend(nr.pontos)
        combined.pets.extend(nr.pets)
        combined.feed.extend(nr.feed)
        combined.outros.extend(nr.outros)
    return combined


# ---------------------------------------------------------------------------
# per-portal normalizers
# ---------------------------------------------------------------------------


def _emergencia_mg(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for item in r.data.get("emergency_contacts", []):
        raw_id = hashlib.md5(
            (str(item.get("nome", "")) + str(item.get("telefone", ""))).encode()
        ).hexdigest()[:8]
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
        raw_id = hashlib.md5(
            (str(item.get("titulo", "")) + str(item.get("url", ""))).encode()
        ).hexdigest()[:8]
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
        raw_id = hashlib.md5(str(item.get("nome", "")).encode()).hexdigest()[:8]
        lat, lng = _geo(item)
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
        raw_id = hashlib.md5(
            (str(item.get("nome", "")) + str(item.get("telefone", ""))).encode()
        ).hexdigest()[:8]
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


_NORMALIZERS["01-emergencia-mg"] = _emergencia_mg


# ---------------------------------------------------------------------------


def _sos_animais_mg(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    tipo_map = {
        "lost": "perdido",
        "found": "encontrado",
        "adoption": "adocao",
    }
    for category, tipo in tipo_map.items():
        for item in r.data.get(category, []):
            city = _city_slug(item, "city", fallback="mg")
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


_NORMALIZERS["03-sos-animais-mg"] = _sos_animais_mg


# ---------------------------------------------------------------------------


def _sos_minas_growberry(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for item in r.data.get("pedidos", []):
        raw_id = _first(item, "id", "ID", "codigo") or ""
        city = _city_slug(item, "cidade", fallback="mg")
        lat, lng = _geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                titulo=_first(item, "titulo", "title", "descricao"),
                descricao=_first(item, "descricao", "description", "detalhe"),
                categoria=_first(item, "categoria", "tipo"),
                status=item.get("status"),
                contato=_first(item, "telefone", "phone", "contato", "whatsapp"),
                cidade=item.get("cidade"),
                bairro=_first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("voluntarios", []):
        raw_id = _first(item, "id", "ID") or ""
        city = _city_slug(item, "cidade", fallback="mg")
        lat, lng = _geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                nome=_first(item, "nome", "name"),
                descricao=_first(item, "descricao", "description", "habilidades"),
                categoria=item.get("categoria") or item.get("area"),
                contato=_first(item, "telefone", "phone", "contato", "whatsapp"),
                cidade=item.get("cidade"),
                bairro=_first(item, "bairro", "neighborhood", "logradouro"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("doacoes", [])):
        raw_id = _first(item, "id", "ID") or str(i)
        city = _city_slug(item, "cidade", fallback="mg")
        lat, lng = _geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                tipo="doacao",
                nome=_first(item, "nome", "name", "titulo"),
                endereco=_first(item, "endereco", "address"),
                cidade=item.get("cidade"),
                bairro=_first(item, "bairro", "neighborhood"),
                contato=_first(item, "telefone", "phone", "contato"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr


_NORMALIZERS["05-sos-minas-growberry"] = _sos_minas_growberry


# ---------------------------------------------------------------------------


def _sosjf_org(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

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
                    titulo=_first(item, "titulo", "title", "name"),
                    descricao=_first(
                        item, "descricao", "description", "content", "body"
                    ),
                    url=_first(item, "url", "link", "href"),
                    data=str(item["date"]) if item.get("date") else None,
                    urgente=bool(item.get("urgente") or item.get("urgent")),
                    raw=item,
                )
            )

    return nr


_NORMALIZERS["06-sosjf-org"] = _sosjf_org


# ---------------------------------------------------------------------------


def _sosjf_online(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    tipo_map = {
        "collection_points": "coleta",
        "shelters": "abrigo",
    }
    for key, tipo in tipo_map.items():
        for i, item in enumerate(r.data.get(key, [])):
            raw_id = _first(item, "id", "ID") or str(i)
            bairro = item.get("neighborhood") or item.get("bairro")
            lat, lng = _geo(item)
            if lat is None and isinstance(item.get("location"), dict):
                lat, lng = _geo(item["location"])
            nr.pontos.append(
                PontoAjuda(
                    id=f"{pid}:jf:{raw_id}",
                    **base,
                    tipo=tipo,
                    nome=_first(item, "name", "nome"),
                    endereco=_first(item, "address", "endereco"),
                    bairro=bairro,
                    cidade="Juiz de Fora",
                    contato=_first(item, "phone", "telefone", "contato"),
                    horario=_first(item, "horario", "hours"),
                    itens=item.get("acceptedItems")
                    or item.get("itens")
                    or item.get("items")
                    or [],
                    lat=lat,
                    lng=lng,
                    raw=item,
                )
            )

    return nr


_NORMALIZERS["07-sosjf-online"] = _sosjf_online


# ---------------------------------------------------------------------------


def _ajude_io(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    def _ajude_geo(item: dict) -> tuple[float | None, float | None]:
        lat, lng = _geo(item)
        if lat is None and isinstance(item.get("localizacao"), dict):
            lat, lng = _geo(item["localizacao"])
        return lat, lng

    for item in r.data.get("help_requests", []):
        raw_id = item.get("id", "")
        city = _city_slug(item, "cidade", "city", fallback="jf")
        lat, lng = _ajude_geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                titulo=_first(item, "titulo", "title", "tipo"),
                descricao=_first(item, "descricao", "description", "detalhes"),
                categoria=_first(item, "categoria", "tipo", "category"),
                status=item.get("status"),
                nome=_first(item, "nome", "name", "solicitante"),
                contato=_first(item, "telefone", "phone", "contato", "whatsapp"),
                cidade=_first(item, "cidade", "city"),
                bairro=_first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("volunteer_offers", []):
        raw_id = item.get("id", "")
        city = _city_slug(item, "cidade", "city", fallback="jf")
        lat, lng = _ajude_geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                nome=_first(item, "nome", "name"),
                descricao=_first(item, "descricao", "description", "habilidades"),
                categoria=_first(item, "categoria", "tipo", "category"),
                contato=_first(item, "telefone", "phone", "contato"),
                cidade=_first(item, "cidade", "city"),
                bairro=_first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("donation_points", [])):
        raw_id = item.get("id") or str(i)
        city = _city_slug(item, "cidade", "city", fallback="jf")
        lat, lng = _ajude_geo(item)
        itens_raw = (
            item.get("itens") or item.get("items") or item.get("necessidades") or []
        )
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                tipo="doacao",
                nome=_first(item, "nome", "name"),
                endereco=_first(item, "endereco", "address"),
                cidade=_first(item, "cidade", "city"),
                bairro=_first(item, "bairro", "neighborhood"),
                contato=_first(item, "telefone", "phone", "contato"),
                horario=_first(item, "horario", "hours"),
                itens=itens_raw if isinstance(itens_raw, list) else [str(itens_raw)],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("shelters", [])):
        raw_id = item.get("id") or item.get("name") or str(i)
        lat, lng = _geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:abrigo:{raw_id}",
                **base,
                tipo="abrigo",
                nome=item.get("name") or item.get("nome"),
                bairro=item.get("neighborhood") or item.get("bairro"),
                cidade="Juiz de Fora",
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr


_NORMALIZERS["08-ajude-io"] = _ajude_io


# ---------------------------------------------------------------------------


def _cidade_que_cuida(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    def _users(item: dict[str, Any]) -> dict[str, Any]:
        u = item.get("users")
        return u if isinstance(u, dict) else {}

    for item in r.data.get("pedidos", []):
        raw_id = item.get("id", "")
        u = _users(item)
        lat, lng = _geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:jf:{raw_id}",
                **base,
                titulo=_first(item, "titulo", "title"),
                descricao=_first(item, "descricao", "description"),
                categoria=_first(item, "categoria", "tipo"),
                status=item.get("status"),
                nome=u.get("nome"),
                contato=u.get("telefone") or _first(item, "telefone", "phone"),
                cidade="Juiz de Fora",
                bairro=_first(item, "bairro") or u.get("bairro"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("voluntarios", []):
        raw_id = item.get("id", "")
        u = _users(item)
        lat, lng = _geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:jf:{raw_id}",
                **base,
                nome=u.get("nome") or _first(item, "nome"),
                descricao=_first(item, "descricao", "description", "titulo", "title"),
                categoria=_first(item, "categoria", "tipo"),
                contato=u.get("telefone") or _first(item, "telefone"),
                cidade="Juiz de Fora",
                bairro=_first(item, "bairro") or u.get("bairro"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("doacoes", []):
        raw_id = item.get("id", "")
        u = _users(item)
        lat, lng = _geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:{raw_id}",
                **base,
                tipo="doacao",
                nome=_first(item, "titulo", "title"),
                descricao=_first(item, "descricao", "description"),
                cidade="Juiz de Fora",
                bairro=_first(item, "bairro") or u.get("bairro"),
                contato=u.get("telefone") or _first(item, "telefone"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for item in r.data.get("entidades", []):
        raw_id = item.get("id", "")
        lat, lng = _geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:entidade:{raw_id}",
                **base,
                tipo="entidade",
                nome=_first(item, "nome", "name", "titulo"),
                endereco=_first(item, "endereco", "address"),
                cidade="Juiz de Fora",
                bairro=_first(item, "bairro", "neighborhood"),
                contato=_first(item, "telefone", "phone", "contato"),
                horario=_first(item, "horario", "horarios"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr


_NORMALIZERS["09-cidade-que-cuida"] = _cidade_que_cuida


# ---------------------------------------------------------------------------


def _minas_emergencia(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for i, item in enumerate(r.data.get("pontos", [])):
        raw_id = _first(item, "id", "ID") or str(i)
        city = _city_slug(item, "cidade", fallback="mg")
        lat, lng = _geo(item)
        itens_raw = item.get("itens") or []
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                tipo=item.get("tipo") or "ponto",
                nome=item.get("nome"),
                endereco=item.get("endereco"),
                cidade=item.get("cidade"),
                bairro=item.get("bairro"),
                contato=item.get("contato"),
                horario=item.get("horario"),
                itens=itens_raw if isinstance(itens_raw, list) else [],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr


_NORMALIZERS["02-minas-emergencia"] = _minas_emergencia


# ---------------------------------------------------------------------------


def _ajude_juiz_de_fora(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for i, item in enumerate(r.data.get("collection_points", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = _geo(item)
        itens_raw = item.get("items") or item.get("itens") or []
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:{raw_id}",
                **base,
                tipo="coleta",
                nome=_first(item, "name", "nome"),
                endereco=_first(item, "address", "endereco"),
                cidade=_first(item, "city", "cidade") or "Juiz de Fora",
                bairro=_first(item, "neighborhood", "bairro"),
                contato=_first(item, "phone", "telefone", "contato"),
                horario=_first(item, "hours", "horario"),
                itens=itens_raw if isinstance(itens_raw, list) else [str(itens_raw)],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("needs", [])):
        raw_id = item.get("id") or str(i)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:jf:{raw_id}",
                **base,
                titulo=_first(item, "category", "custom_label"),
                descricao=_first(item, "custom_label", "category"),
                categoria=item.get("category"),
                status="ativo" if item.get("is_active") else "inativo",
                cidade="Juiz de Fora",
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("reports", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = _geo(item)
        nr.feed.append(
            FeedItem(
                id=f"{pid}:jf:report:{raw_id}",
                **base,
                tipo="relatorio",
                titulo=_first(item, "type", "address"),
                descricao=_first(item, "description", "reference"),
                data=str(item.get("created_at") or ""),
                raw=item,
            )
        )

    return nr


_NORMALIZERS["10-ajude-juiz-de-fora"] = _ajude_juiz_de_fora


# ---------------------------------------------------------------------------


def _sos_ser_luz_jf(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    form_info = r.data.get("form_fields", {})
    if form_info.get("available"):
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:form_structure",
                **base,
                tipo="formulario",
                titulo="Formulário de Pedido de Ajuda",
                descricao=r.data.get("note", ""),
                url=f"{purl}/help_requests/new",
                raw=form_info,
            )
        )

    return nr


_NORMALIZERS["11-sos-ser-luz-jf"] = _sos_ser_luz_jf


# ---------------------------------------------------------------------------


def _ajuda_imediata(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for item in r.data.get("items", []):
        raw_id = item.get("id") or ""
        tipo_pub = item.get("tipo_publicacao", "")
        u = item.get("usuario") or {}
        nome = u.get("nome") or _first(item, "nome", "name")
        contato = u.get("telefone") or _first(item, "telefone", "whatsapp")
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


_NORMALIZERS["12-ajuda-imediata"] = _ajuda_imediata


# ---------------------------------------------------------------------------


def _ajuda_jf_arctei(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for i, item in enumerate(r.data.get("requests", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = _geo(item)
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
        lat, lng = _geo(item)
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
        lat, lng = _geo(item)
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


_NORMALIZERS["13-ajuda-jf-arctei"] = _ajuda_jf_arctei


# ---------------------------------------------------------------------------


def _onde_doar(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for i, item in enumerate(r.data.get("donation_points", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = _geo(item)
        # Extrair categorias do array de objetos aninhados
        cats = item.get("categorias") or []
        itens = [
            c["categoria"]["nome"]
            for c in cats
            if isinstance(c, dict) and isinstance(c.get("categoria"), dict)
        ]
        _ender_parts = [p for p in [item.get("endereco"), item.get("numero")] if p]
        endereco = ", ".join(_ender_parts) or None
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:{raw_id}",
                **base,
                tipo="doacao",
                nome=item.get("nome"),
                descricao=item.get("detalhes"),
                endereco=endereco,
                cidade=item.get("cidade") or "Juiz de Fora",
                contato=item.get("telefone") or item.get("whatsapp"),
                itens=itens,
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("help_requests", [])):
        raw_id = _first(item, "id", "ID") or str(i)
        lat, lng = _geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:jf:pedido:{raw_id}",
                **base,
                titulo=_first(item, "titulo", "title"),
                descricao=_first(item, "descricao", "description"),
                categoria=_first(item, "categoria", "tipo"),
                status=item.get("status"),
                nome=_first(item, "nome", "name"),
                contato=_first(item, "telefone", "phone", "contato"),
                cidade=_first(item, "cidade", "city") or "Juiz de Fora",
                bairro=_first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr


_NORMALIZERS["15-onde-doar"] = _onde_doar


# ---------------------------------------------------------------------------


def _interdicoes_jf(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for item in r.data.get("interdicoes", []):
        key = f"{item.get('Endereco', '')}:{item.get('Data_Registro', '')}:{item.get('Hora_registro', '')}"
        raw_id = hashlib.md5(key.encode()).hexdigest()[:8]
        status = item.get("Status", "")
        endereco = item.get("Endereco") or ""
        zona = item.get("Zona") or ""
        titulo = f"{endereco} ({zona})" if zona else endereco
        nr.feed.append(
            FeedItem(
                id=f"{pid}:jf:interdicao:{raw_id}",
                **base,
                tipo="interdicao",
                titulo=titulo or None,
                descricao=item.get("Descricao"),
                data=item.get("Data_Registro") or "",
                urgente=status == "INTERDITADA",
                raw=item,
            )
        )

    return nr


_NORMALIZERS["16-interdicoes-jf"] = _interdicoes_jf


# ---------------------------------------------------------------------------


def _ajuda_emjf(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for i, item in enumerate(r.data.get("collection_points", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = _geo(item)
        itens_raw = item.get("items") or item.get("itens") or []
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:coleta:{raw_id}",
                **base,
                tipo="coleta",
                nome=_first(item, "name", "nome"),
                endereco=_first(item, "address", "endereco"),
                cidade=_first(item, "city", "cidade") or "Juiz de Fora",
                bairro=_first(item, "neighborhood", "bairro"),
                contato=_first(item, "phone", "telefone", "contato"),
                horario=_first(item, "hours", "horario"),
                itens=itens_raw if isinstance(itens_raw, list) else [str(itens_raw)],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("shelters", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = _geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:abrigo:{raw_id}",
                **base,
                tipo="abrigo",
                nome=_first(item, "name", "nome"),
                endereco=_first(item, "address", "endereco"),
                cidade=_first(item, "city", "cidade") or "Juiz de Fora",
                bairro=_first(item, "neighborhood", "bairro"),
                contato=_first(item, "phone", "telefone", "contato"),
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
                titulo=_first(item, "name", "nome"),
                descricao=_first(item, "description", "descricao"),
                contato=_first(item, "pixKey", "pix_key", "chave_pix"),
                raw=item,
            )
        )

    return nr


_NORMALIZERS["17-ajuda-emjf"] = _ajuda_emjf


# ---------------------------------------------------------------------------


def _mi_au_ajuda(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for i, item in enumerate(r.data.get("acolhedores", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = _geo(item)
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
        city = _city_slug(item, "cidade", "city", fallback="jf")
        nr.pets.append(
            Pet(
                id=f"{pid}:{city}:{raw_id}",
                **base,
                tipo=_first(item, "tipo", "type") or "perdido",
                nome=_first(item, "nome", "name", "nome_pet"),
                especie=_first(item, "especie", "animal_type", "tipo_animal"),
                porte=_first(item, "porte", "size"),
                descricao=_first(item, "descricao", "description"),
                status=item.get("status"),
                contato=_first(item, "telefone", "phone", "contato"),
                cidade=_first(item, "cidade", "city"),
                bairro=_first(item, "bairro", "neighborhood"),
                imagem_url=_first(item, "imagem_url", "image_url", "foto"),
                raw=item,
            )
        )

    return nr


_NORMALIZERS["18-mi-au-ajuda"] = _mi_au_ajuda


# ---------------------------------------------------------------------------


def _zona_da_mata_alertas(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for i, item in enumerate(r.data.get("alerts", [])):
        raw_id = item.get("id") or str(i)
        alert_type = item.get("type") or ""
        nr.feed.append(
            FeedItem(
                id=f"{pid}:zona_da_mata:{raw_id}",
                **base,
                tipo="alerta",
                titulo=alert_type or "alerta",
                descricao=_first(item, "description", "descricao", "message"),
                data=str(item.get("created_at") or ""),
                raw=item,
            )
        )

    return nr


_NORMALIZERS["19-zona-da-mata-alertas"] = _zona_da_mata_alertas


# ---------------------------------------------------------------------------


def _unidos_por_jf(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    for i, item in enumerate(r.data.get("pedidos", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = _geo(item)
        nr.pedidos.append(
            Pedido(
                id=f"{pid}:jf:{raw_id}",
                **base,
                titulo=item.get("need_type") or item.get("description"),
                descricao=item.get("description"),
                categoria=item.get("need_type"),
                status=item.get("status"),
                nome=item.get("name"),
                contato=item.get("phone"),
                cidade="Juiz de Fora",
                bairro=item.get("neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    for i, item in enumerate(r.data.get("voluntarios", [])):
        raw_id = item.get("id") or str(i)
        lat, lng = _geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:jf:{raw_id}",
                **base,
                nome=item.get("name"),
                descricao=item.get("description"),
                categoria=item.get("need_type"),
                contato=item.get("phone"),
                cidade="Juiz de Fora",
                bairro=item.get("neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    return nr


_NORMALIZERS["20-unidos-por-jf"] = _unidos_por_jf


# ---------------------------------------------------------------------------


def _ajude_jf(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

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
                descricao=_first(item, "descricao", "cor"),
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
        city = _city_slug(item, "cidade", "city", fallback="jf")
        lat, lng = _geo(item)
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:{city}:lar:{raw_id}",
                **base,
                nome=_first(item, "nome", "name"),
                descricao=_first(item, "descricao", "description", "observacao"),
                categoria="lar_temporario",
                contato=_first(item, "telefone", "phone", "contato", "whatsapp"),
                cidade=_first(item, "cidade", "city"),
                bairro=_first(item, "bairro", "neighborhood"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    # Doadores → voluntário (categoria: doador)
    for item in r.data.get("doadores_public", []):
        raw_id = item.get("id") or ""
        city = _city_slug(item, "cidade", "city", fallback="jf")
        nr.voluntarios.append(
            Voluntario(
                id=f"{pid}:{city}:doador:{raw_id}",
                **base,
                nome=_first(item, "nome", "name"),
                descricao=_first(item, "descricao", "description"),
                categoria="doador",
                contato=_first(item, "telefone", "phone", "contato"),
                cidade=_first(item, "cidade", "city"),
                bairro=_first(item, "bairro", "neighborhood"),
                raw=item,
            )
        )

    # ONGs / protetores → ponto (tipo: entidade)
    for item in r.data.get("ongs_protetores", []):
        raw_id = item.get("id") or ""
        lat, lng = _geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:ong:{raw_id}",
                **base,
                tipo="entidade",
                nome=_first(item, "nome", "name"),
                descricao=_first(item, "descricao", "description"),
                endereco=_first(item, "endereco", "address"),
                cidade=_first(item, "cidade", "city") or "Juiz de Fora",
                bairro=_first(item, "bairro", "neighborhood"),
                contato=_first(item, "telefone", "phone", "contato"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    # Pontos de doação
    for item in r.data.get("pontos_doacao", []):
        raw_id = item.get("id") or ""
        lat, lng = _geo(item)
        itens_raw = item.get("itens") or item.get("items") or []
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:doacao:{raw_id}",
                **base,
                tipo="doacao",
                nome=_first(item, "nome", "name"),
                endereco=_first(item, "endereco", "address"),
                cidade=_first(item, "cidade", "city") or "Juiz de Fora",
                bairro=_first(item, "bairro", "neighborhood"),
                contato=_first(item, "telefone", "phone", "contato"),
                horario=_first(item, "horario", "hours"),
                itens=itens_raw if isinstance(itens_raw, list) else [str(itens_raw)],
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    # Pontos de alimentação
    for item in r.data.get("pontos_alimentacao", []):
        raw_id = item.get("id") or ""
        lat, lng = _geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:alimentacao:{raw_id}",
                **base,
                tipo="alimentacao",
                nome=_first(item, "nome", "name"),
                endereco=_first(item, "endereco", "address"),
                cidade=_first(item, "cidade", "city") or "Juiz de Fora",
                bairro=_first(item, "bairro", "neighborhood"),
                contato=_first(item, "telefone", "phone", "contato"),
                horario=_first(item, "horario", "hours"),
                lat=lat,
                lng=lng,
                raw=item,
            )
        )

    # Abrigos
    for item in r.data.get("abrigos", []):
        raw_id = item.get("id") or ""
        lat, lng = _geo(item)
        nr.pontos.append(
            PontoAjuda(
                id=f"{pid}:jf:abrigo:{raw_id}",
                **base,
                tipo="abrigo",
                nome=_first(item, "nome", "name"),
                endereco=_first(item, "endereco", "address"),
                cidade=_first(item, "cidade", "city") or "Juiz de Fora",
                bairro=_first(item, "bairro", "neighborhood"),
                contato=_first(item, "telefone", "phone", "contato"),
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
                titulo=_first(item, "titulo", "title", "nome"),
                descricao=_first(item, "descricao", "description"),
                url=_first(item, "url", "link"),
                raw=item,
            )
        )

    return nr


_NORMALIZERS["21-ajude-jf"] = _ajude_jf


# ---------------------------------------------------------------------------


def _conta_publica(r: ScraperResult) -> NormalizedResult:
    nr = NormalizedResult()
    pid, pname, purl, sa = r.portal_id, r.portal_name, r.url, r.scraped_at
    base = dict(portal_id=pid, portal_name=pname, portal_url=purl, scraped_at=sa)

    saldo = r.data.get("saldo")
    if saldo and isinstance(saldo, dict):
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:saldo",
                **base,
                tipo="saldo",
                titulo="Saldo Conta Pública",
                descricao=str(
                    saldo.get("saldo")
                    or saldo.get("valor")
                    or saldo.get("saldoTotal")
                    or saldo.get("totalArrecadado")
                    or ""
                ),
                raw=saldo,
            )
        )

    for i, item in enumerate(r.data.get("extrato", [])):
        raw_id = item.get("id") or str(i)
        nr.feed.append(
            FeedItem(
                id=f"{pid}:jf:extrato:{raw_id}",
                **base,
                tipo="transacao",
                titulo=_first(item, "descricao", "description", "tipo"),
                descricao=_first(item, "detalhe", "detalhes", "observacao"),
                data=str(_first(item, "data", "date", "created_at") or ""),
                raw=item,
            )
        )

    registro = r.data.get("registro")
    if registro and isinstance(registro, dict):
        nr.outros.append(
            Outro(
                id=f"{pid}:jf:registro",
                **base,
                tipo="registro",
                titulo="Registro Conta Pública",
                descricao=str(_first(registro, "descricao", "description") or ""),
                raw=registro,
            )
        )

    return nr


_NORMALIZERS["22-conta-publica"] = _conta_publica
