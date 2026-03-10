from __future__ import annotations

import asyncio
import json
from typing import Any

from app.scrapers.base import BaseScraper, ScraperResult

CITIES: list[str] = ["jf", "uba", "matias-barbosa", "cataguases"]

CITY_SLUG_TO_NAME: dict[str, str] = {
    "jf": "Juiz de Fora",
    "uba": "Ubá",
    "matias-barbosa": "Matias Barbosa",
    "cataguases": "Cataguases",
}


def _extract_pontos_from_firestore_response(
    body: bytes, cidade: str
) -> list[dict[str, Any]]:
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []

    pontos: list[dict[str, Any]] = []

    documents: list[Any] = []
    if isinstance(payload, dict):
        documents = payload.get("documents", [])
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, list):
                for sub in item:
                    if isinstance(sub, dict) and "documents" in sub:
                        documents.extend(sub["documents"])
            elif isinstance(item, dict) and "documents" in item:
                documents.extend(item["documents"])

    for doc in documents:
        fields = doc.get("fields", {})
        ponto = _parse_firestore_fields(fields, cidade)
        if ponto:
            pontos.append(ponto)

    return pontos


def _firestore_value(field: dict[str, Any]) -> Any:
    if not isinstance(field, dict):
        return field
    for vtype in (
        "stringValue",
        "integerValue",
        "doubleValue",
        "booleanValue",
        "nullValue",
    ):
        if vtype in field:
            return field[vtype]
    if "arrayValue" in field:
        values = field["arrayValue"].get("values", [])
        return [_firestore_value(v) for v in values]
    if "mapValue" in field:
        nested = field["mapValue"].get("fields", {})
        return {k: _firestore_value(v) for k, v in nested.items()}
    if "geoPointValue" in field:
        gp = field["geoPointValue"]
        return {"lat": gp.get("latitude"), "lng": gp.get("longitude")}
    return None


def _parse_firestore_fields(
    fields: dict[str, Any], cidade: str
) -> dict[str, Any] | None:
    if not fields:
        return None

    def get(key: str) -> Any:
        for candidate in (key, key.lower(), key.upper()):
            if candidate in fields:
                return _firestore_value(fields[candidate])
        return None

    lat: float | None = None
    lng: float | None = None

    geo = get("coordenadas") or get("geopoint") or get("location") or get("localizacao")
    if isinstance(geo, dict):
        lat = geo.get("lat") or geo.get("latitude")
        lng = geo.get("lng") or geo.get("longitude")

    if lat is None:
        lat = get("lat") or get("latitude")
    if lng is None:
        lng = get("lng") or get("longitude")

    itens_raw = get("itens") or get("items") or get("necessidades") or []
    itens: list[str] = itens_raw if isinstance(itens_raw, list) else [str(itens_raw)]

    return {
        "nome": get("nome") or get("name") or get("titulo") or "",
        "endereco": get("endereco") or get("address") or get("logradouro") or "",
        "tipo": get("tipo") or get("type") or get("categoria") or "",
        "lat": lat,
        "lng": lng,
        "itens": itens,
        "contato": get("contato")
        or get("telefone")
        or get("phone")
        or get("contact")
        or "",
        "horario": get("horario") or get("horarios") or get("funcionamento") or "",
        "cidade": cidade,
    }


def _extract_pontos_from_dom(dom_text: str, cidade: str) -> list[dict[str, Any]]:
    """Best-effort DOM fallback: extract JSON blobs embedded in Next.js __NEXT_DATA__."""
    import re

    pontos: list[dict[str, Any]] = []

    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', dom_text, re.DOTALL
    )
    if not match:
        return pontos

    try:
        next_data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return pontos

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                if isinstance(item, dict):
                    if "nome" in item or "name" in item or "endereco" in item:
                        ponto = _parse_firestore_fields(
                            {
                                k: {"stringValue": v}
                                if isinstance(v, str)
                                else {"doubleValue": v}
                                for k, v in item.items()
                            },
                            cidade,
                        )
                        if ponto:
                            pontos.append(ponto)
                    else:
                        walk(item)
                else:
                    walk(item)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)

    walk(next_data)
    return pontos


class MinasEmergenciaScraper(BaseScraper):
    portal_id: str = "02-minas-emergencia"
    portal_name: str = "Minas Emergência"
    base_url: str = "https://minas-emergencia.com"

    async def get_pontos_cidade(self, city_slug: str) -> list[dict[str, Any]]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "playwright não instalado — instale com: pip install playwright && playwright install chromium"
            )

        url = f"{self.base_url}/{city_slug}"
        cidade = CITY_SLUG_TO_NAME.get(city_slug, city_slug)
        pontos: list[dict[str, Any]] = []
        firestore_bodies: list[bytes] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=self.DEFAULT_HEADERS["User-Agent"],
                locale="pt-BR",
                extra_http_headers={
                    "Accept-Language": self.DEFAULT_HEADERS["Accept-Language"],
                },
            )
            page = await context.new_page()

            async def handle_response(response: Any) -> None:
                if "firestore.googleapis.com" in response.url:
                    try:
                        body = await response.body()
                        firestore_bodies.append(body)
                    except Exception:
                        pass

            page.on("response", handle_response)

            await page.goto(url, wait_until="networkidle", timeout=60_000)

            loading_selectors = [
                "text=Carregando pontos",
                "text=Carregando...",
                "[data-testid='loading']",
                ".loading",
                "#loading",
            ]
            for sel in loading_selectors:
                try:
                    await page.wait_for_selector(sel, state="hidden", timeout=15_000)
                    break
                except Exception:
                    pass

            card_selectors = [
                "[data-testid='ponto-card']",
                ".ponto-card",
                ".marker-card",
                ".card",
                "article",
                "[class*='card']",
                "[class*='ponto']",
                "[class*='marker']",
            ]
            for sel in card_selectors:
                try:
                    await page.wait_for_selector(sel, timeout=10_000)
                    break
                except Exception:
                    pass

            await asyncio.sleep(2)

            for body in firestore_bodies:
                extracted = _extract_pontos_from_firestore_response(body, cidade)
                pontos.extend(extracted)

            if not pontos:
                dom_text = await page.content()
                pontos = _extract_pontos_from_dom(dom_text, cidade)

            await browser.close()

        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for p in pontos:
            key = f"{p.get('nome')}|{p.get('endereco')}|{p.get('lat')}|{p.get('lng')}"
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique

    async def get_pontos_jf(self) -> list[dict[str, Any]]:
        return await self.get_pontos_cidade("jf")

    async def get_pontos_uba(self) -> list[dict[str, Any]]:
        return await self.get_pontos_cidade("uba")

    async def get_pontos_matias_barbosa(self) -> list[dict[str, Any]]:
        return await self.get_pontos_cidade("matias-barbosa")

    async def get_pontos_cataguases(self) -> list[dict[str, Any]]:
        return await self.get_pontos_cidade("cataguases")

    async def scrape(self) -> ScraperResult:
        result = self.create_result()
        all_pontos: list[dict[str, Any]] = []

        for city_slug in CITIES:
            try:
                pontos = await self.get_pontos_cidade(city_slug)
                all_pontos.extend(pontos)
            except RuntimeError as exc:
                result.errors.append(str(exc))
                break
            except Exception as exc:
                result.errors.append(f"{city_slug}: {exc}")

        result.data = {"pontos": all_pontos}
        return result
