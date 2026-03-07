import asyncio
import json

from app.scrapers.base import BaseScraper, ScraperResult

APPS_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbwXjWoPo48vMVLNb_bccZsdhcQ9Rg260-xr_nzc6yZT5387dcTOqiv2wi5PHmoF03Dv/exec"
)


class AjudaJfArcteiScraper(BaseScraper):
    portal_id = "13-ajuda-jf-arctei"
    portal_name = "Ajuda JF (Arctei)"
    base_url = "https://ajudajf.arctei.com.br"

    async def _fetch_action(self, action: str) -> list[dict]:
        async with self.get_client() as client:
            response = await client.get(APPS_SCRIPT_URL, params={"action": action})
            response.raise_for_status()
            text = response.text

            # Google Apps Script may return JSONP-wrapped or plain JSON
            if text.startswith("//"):
                text = text.split("\n", 1)[-1]
            if text.startswith("(") or text.startswith("callback("):
                text = text[text.index("(") + 1 : text.rindex(")")]

            payload = json.loads(text)
            if isinstance(payload, dict) and "data" in payload:
                return payload["data"]
            if isinstance(payload, list):
                return payload
            return []

    async def get_requests(self) -> list[dict]:
        return await self._fetch_action("listRequests")

    async def get_points(self) -> list[dict]:
        return await self._fetch_action("listPoints")

    async def get_volunteers(self) -> list[dict]:
        return await self._fetch_action("listVolunteers")

    async def get_vistorias(self) -> list[dict]:
        return await self._fetch_action("listVistorias")

    async def scrape(self) -> ScraperResult:
        result = ScraperResult(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            url=self.base_url,
        )

        actions = ["listRequests", "listPoints", "listVolunteers", "listVistorias"]
        keys = ["requests", "points", "volunteers", "vistorias"]

        responses = await asyncio.gather(
            *[self._fetch_action(a) for a in actions],
            return_exceptions=True,
        )

        for key, res in zip(keys, responses, strict=True):
            if isinstance(res, Exception):
                result.errors.append(f"{key}: {res}")
                result.data[key] = []
            else:
                result.data[key] = res

        return result
