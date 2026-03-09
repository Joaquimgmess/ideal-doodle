from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx


class ScraperStatus(str, Enum):
    SUCCESS = "success"  # dados coletados sem erros
    PARTIAL = "partial"  # dados coletados com erros parciais
    EMPTY = "empty"  # sem dados (legítimo, portal vazio)
    ERROR = "error"  # falha total


@dataclass
class ScraperResult:
    portal_id: str
    portal_name: str
    url: str
    status: ScraperStatus = ScraperStatus.SUCCESS
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class BaseScraper(ABC):
    portal_id: str
    portal_name: str
    base_url: str

    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": "SOS-JF-Scraper/1.0 (+https://sosjf.com.br)",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    def get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers=self.DEFAULT_HEADERS,
            timeout=30.0,
            follow_redirects=True,
        )

    @abstractmethod
    async def scrape(self) -> ScraperResult:
        """Executa todos os métodos de raspagem e retorna resultado consolidado."""
        ...
