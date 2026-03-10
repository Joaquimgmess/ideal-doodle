"""Testes de integração para scrapers com mocks HTTP (respx)."""

import pytest
import respx
from httpx import Response

from app.scrapers.base import ScraperStatus
from app.scrapers.emergencia_mg import EmergenciaMgScraper
from app.scrapers.sosjf_org import SosJfOrgScraper

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# SosJfOrgScraper — REST API simples
# ---------------------------------------------------------------------------


class TestSosJfOrgScraper:
    @respx.mock
    async def test_scrape_success(self):
        alerts_data = [
            {"id": "alert-1", "title": "Alerta chuva", "date": "2026-01-01"},
            {"id": "news-1", "title": "Notícia", "date": "2026-01-01"},
        ]
        reports_data = [{"id": "report-1", "title": "Relatório"}]

        respx.get("https://sosjf.org/api/alerts").mock(
            return_value=Response(200, json=alerts_data)
        )
        respx.get("https://sosjf.org/api/reports").mock(
            return_value=Response(200, json=reports_data)
        )

        scraper = SosJfOrgScraper()
        result = await scraper.scrape()
        result.resolve_status()

        assert result.status == ScraperStatus.SUCCESS
        assert len(result.data["alerts"]) == 1
        assert len(result.data["news"]) == 1
        assert len(result.data["reports"]) == 1
        assert result.errors == []

    @respx.mock
    async def test_scrape_partial_failure(self):
        respx.get("https://sosjf.org/api/alerts").mock(
            return_value=Response(200, json=[])
        )
        respx.get("https://sosjf.org/api/reports").mock(return_value=Response(500))

        scraper = SosJfOrgScraper()
        result = await scraper.scrape()
        result.resolve_status()

        assert result.status == ScraperStatus.ERROR
        assert len(result.errors) == 1
        assert "reports" in result.errors[0]

    @respx.mock
    async def test_scrape_total_failure(self):
        respx.get("https://sosjf.org/api/alerts").mock(return_value=Response(500))
        respx.get("https://sosjf.org/api/reports").mock(return_value=Response(500))

        scraper = SosJfOrgScraper()
        result = await scraper.scrape()
        result.resolve_status()

        assert result.status == ScraperStatus.ERROR
        assert len(result.errors) == 2

    @respx.mock
    async def test_scrape_empty(self):
        respx.get("https://sosjf.org/api/alerts").mock(
            return_value=Response(200, json=[])
        )
        respx.get("https://sosjf.org/api/reports").mock(
            return_value=Response(200, json=[])
        )

        scraper = SosJfOrgScraper()
        result = await scraper.scrape()
        result.resolve_status()

        assert result.status == ScraperStatus.EMPTY
        assert result.errors == []

    @respx.mock
    async def test_alerts_sorted_by_date(self):
        alerts_data = [
            {"id": "alert-old", "title": "Old", "date": "2025-01-01"},
            {"id": "alert-new", "title": "New", "date": "2026-06-01"},
        ]
        respx.get("https://sosjf.org/api/alerts").mock(
            return_value=Response(200, json=alerts_data)
        )
        respx.get("https://sosjf.org/api/reports").mock(
            return_value=Response(200, json=[])
        )

        scraper = SosJfOrgScraper()
        result = await scraper.scrape()

        assert result.data["alerts"][0]["id"] == "alert-new"
        assert result.data["alerts"][1]["id"] == "alert-old"


# ---------------------------------------------------------------------------
# EmergenciaMgScraper — HTML + static data
# ---------------------------------------------------------------------------


FAKE_HTML_PAGE = """
<html><body>
<div class="section">
  <span class="section-label">Ajuda</span>
  <a class="link-card" href="https://example.com/donate">
    <span class="card-title">Doações</span>
    <span class="card-desc">Doe aqui</span>
  </a>
</div>
</body></html>
"""

FAKE_LARES_HTML = """
<html><body>
<div class="contact-card lar">
  <span class="card-title">Abrigo Feliz</span>
  <span class="card-desc">32999999999</span>
  <span class="tag tag-dog"></span>
  <a href="https://wa.me/32999999999">WhatsApp</a>
</div>
<div class="contact-card transporte">
  <span class="card-title">João Motorista</span>
  <span class="card-desc">32888888888</span>
  <a href="https://wa.me/32888888888">WhatsApp</a>
</div>
</body></html>
"""


class TestEmergenciaMgScraper:
    async def test_scrape_success(self):
        with respx.mock:
            respx.get("https://emergencia-mg.netlify.app/").mock(
                return_value=Response(200, text=FAKE_HTML_PAGE)
            )
            # animal_shelters e transport_volunteers buscam a mesma URL
            respx.get("https://emergencia-mg.netlify.app/lares-temporarios").mock(
                return_value=Response(200, text=FAKE_LARES_HTML)
            )

            scraper = EmergenciaMgScraper()
            result = await scraper.scrape()
            result.resolve_status()

        assert result.status == ScraperStatus.SUCCESS
        assert len(result.data["emergency_contacts"]) == 5  # static
        assert len(result.data["help_links"]) == 1
        assert result.data["help_links"][0]["titulo"] == "Doações"
        assert len(result.data["animal_shelters"]) == 1
        assert result.data["animal_shelters"][0]["nome"] == "Abrigo Feliz"
        assert len(result.data["transport_volunteers"]) == 1
        assert result.errors == []

    async def test_scrape_partial_http_failure(self):
        with respx.mock:
            respx.get("https://emergencia-mg.netlify.app/").mock(
                return_value=Response(500)
            )
            respx.get("https://emergencia-mg.netlify.app/lares-temporarios").mock(
                return_value=Response(500)
            )

            scraper = EmergenciaMgScraper()
            result = await scraper.scrape()
            result.resolve_status()

        # emergency_contacts is static, so we still have data
        assert result.status == ScraperStatus.PARTIAL
        assert len(result.data["emergency_contacts"]) == 5
        assert result.data["help_links"] == []
        assert len(result.errors) > 0

    async def test_emergency_contacts_always_present(self):
        """Contatos de emergência são estáticos, não dependem de HTTP."""
        with respx.mock:
            respx.get("https://emergencia-mg.netlify.app/").mock(
                return_value=Response(200, text="<html></html>")
            )
            respx.get("https://emergencia-mg.netlify.app/lares-temporarios").mock(
                return_value=Response(200, text="<html></html>")
            )

            scraper = EmergenciaMgScraper()
            result = await scraper.scrape()

        assert len(result.data["emergency_contacts"]) == 5
        assert result.data["emergency_contacts"][0]["nome"] == "Bombeiros"
