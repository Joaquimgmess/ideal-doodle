"""Testes para scraper_worker: _run_one, _error_result, resolve_status."""

from datetime import datetime, timezone

import httpx
import pytest

from app.scrapers.base import BaseScraper, ScraperResult, ScraperStatus
from app.workers.scraper_worker import _error_result, _run_one

pytestmark = pytest.mark.anyio

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fake scraper for testing
# ---------------------------------------------------------------------------


class FakeScraper(BaseScraper):
    portal_id = "fake-portal"
    portal_name = "Fake Portal"
    base_url = "https://fake.example.com"

    async def scrape(self) -> ScraperResult:
        return ScraperResult(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            url=self.base_url,
            data={"items": [1, 2, 3]},
        )


class FailingScraper(BaseScraper):
    portal_id = "fail-portal"
    portal_name = "Fail Portal"
    base_url = "https://fail.example.com"

    async def scrape(self) -> ScraperResult:
        raise ValueError("something broke")


class TimeoutScraper(BaseScraper):
    portal_id = "timeout-portal"
    portal_name = "Timeout Portal"
    base_url = "https://timeout.example.com"

    async def scrape(self) -> ScraperResult:
        raise httpx.ReadTimeout("timed out")


class HttpErrorScraper(BaseScraper):
    portal_id = "http-error-portal"
    portal_name = "HTTP Error Portal"
    base_url = "https://http-error.example.com"

    async def scrape(self) -> ScraperResult:
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(503, request=request)
        raise httpx.HTTPStatusError("503 error", request=request, response=response)


class ConnectionErrorScraper(BaseScraper):
    portal_id = "conn-error-portal"
    portal_name = "Conn Error Portal"
    base_url = "https://conn-error.example.com"

    async def scrape(self) -> ScraperResult:
        raise httpx.ConnectError("connection refused")


# ---------------------------------------------------------------------------
# _error_result
# ---------------------------------------------------------------------------


class TestErrorResult:
    def test_creates_error_result(self):
        scraper = FakeScraper()
        result = _error_result(scraper, "some error")
        assert result.portal_id == "fake-portal"
        assert result.portal_name == "Fake Portal"
        assert result.url == "https://fake.example.com"
        assert result.status == ScraperStatus.ERROR
        assert result.errors == ["some error"]


# ---------------------------------------------------------------------------
# ScraperResult.resolve_status
# ---------------------------------------------------------------------------


class TestResolveStatus:
    def test_success_with_data(self):
        r = ScraperResult(
            portal_id="p",
            portal_name="P",
            url="http://x",
            data={"items": [1, 2]},
        )
        r.resolve_status()
        assert r.status == ScraperStatus.SUCCESS

    def test_empty_when_no_data(self):
        r = ScraperResult(
            portal_id="p",
            portal_name="P",
            url="http://x",
            data={"items": []},
        )
        r.resolve_status()
        assert r.status == ScraperStatus.EMPTY

    def test_error_when_errors_no_data(self):
        r = ScraperResult(
            portal_id="p",
            portal_name="P",
            url="http://x",
            data={},
            errors=["fail"],
        )
        r.resolve_status()
        assert r.status == ScraperStatus.ERROR

    def test_partial_when_errors_and_data(self):
        r = ScraperResult(
            portal_id="p",
            portal_name="P",
            url="http://x",
            data={"items": [1]},
            errors=["partial fail"],
        )
        r.resolve_status()
        assert r.status == ScraperStatus.PARTIAL

    def test_empty_no_lists_in_data(self):
        r = ScraperResult(
            portal_id="p",
            portal_name="P",
            url="http://x",
            data={"count": 42},
        )
        r.resolve_status()
        assert r.status == ScraperStatus.EMPTY


# ---------------------------------------------------------------------------
# _run_one
# ---------------------------------------------------------------------------


class TestRunOne:
    async def test_success(self):
        result = await _run_one(FakeScraper)
        assert result.status == ScraperStatus.SUCCESS
        assert result.portal_id == "fake-portal"
        assert result.data == {"items": [1, 2, 3]}

    async def test_timeout_returns_error(self):
        result = await _run_one(TimeoutScraper)
        assert result.status == ScraperStatus.ERROR
        assert "timeout" in result.errors[0]

    async def test_http_status_error_returns_error(self):
        result = await _run_one(HttpErrorScraper)
        assert result.status == ScraperStatus.ERROR
        assert "http_503" in result.errors[0]

    async def test_connection_error_returns_error(self):
        result = await _run_one(ConnectionErrorScraper)
        assert result.status == ScraperStatus.ERROR
        assert "connection" in result.errors[0]

    async def test_unexpected_error_returns_error(self):
        result = await _run_one(FailingScraper)
        assert result.status == ScraperStatus.ERROR
        assert "unexpected" in result.errors[0]
        assert "something broke" in result.errors[0]

    async def test_never_raises(self):
        """_run_one deve sempre retornar ScraperResult, nunca levantar exceção."""
        result = await _run_one(FailingScraper)
        assert isinstance(result, ScraperResult)
