"""Helpers compartilhados entre normalizers."""

from __future__ import annotations

import hashlib
from typing import Any


def first(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Retorna o primeiro valor não-nulo/vazio entre as chaves fornecidas."""
    for k in keys:
        v = d.get(k)
        if v is not None and v != "":
            return v
    return default


def geo(d: dict[str, Any]) -> tuple[float | None, float | None]:
    lat = first(d, "lat", "latitude", "Latitude")
    lng = first(d, "lng", "longitude", "lon", "Longitude")
    try:
        return (
            float(lat) if lat is not None else None,
            float(lng) if lng is not None else None,
        )
    except (TypeError, ValueError):
        return None, None


def city_slug(d: dict[str, Any], *keys: str, fallback: str = "mg") -> str:
    v = first(d, *keys) or fallback
    return str(v).lower().replace(" ", "_")


def md5_short(text: str) -> str:
    """Retorna hash MD5 de 8 chars para gerar IDs."""
    return hashlib.md5(text.encode()).hexdigest()[:8]


def base_fields(r: Any) -> dict[str, Any]:
    """Campos comuns para todos os items normalizados."""
    return {
        "portal_id": r.portal_id,
        "portal_name": r.portal_name,
        "portal_url": r.url,
        "scraped_at": r.scraped_at,
    }
