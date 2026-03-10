import json
import re

from app.scrapers.base import BaseScraper, ScraperResult


class OndeDoarScraper(BaseScraper):
    portal_id = "15-onde-doar"
    portal_name = "Onde Doar"
    base_url = "https://ondedoar-io.vercel.app"

    async def _fetch_page(self, path: str) -> str:
        async with self.get_client() as client:
            response = await client.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.text

    def _extract_rsc_pontos(self, html: str) -> list[dict]:
        """Extract donation points from Next.js RSC embedded data."""
        items: list[dict] = []

        for match in re.finditer(
            r'<script[^>]*>self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>',
            html,
            re.DOTALL,
        ):
            chunk = match.group(1)
            try:
                chunk = json.loads(f'"{chunk}"')
            except (json.JSONDecodeError, ValueError):
                continue

            if "statusDoacao" not in chunk:
                continue

            # Find "pontos":[ array in the RSC tree
            pontos_match = re.search(r'"pontos":\s*(\[)', chunk)
            if not pontos_match:
                continue

            arr_start = pontos_match.start(1)
            depth = 0
            arr_end = arr_start
            for i in range(arr_start, len(chunk)):
                if chunk[i] == "[":
                    depth += 1
                elif chunk[i] == "]":
                    depth -= 1
                if depth == 0:
                    arr_end = i + 1
                    break

            try:
                arr_str = chunk[arr_start:arr_end]
                parsed = json.loads(arr_str)
                items.extend(parsed)
            except (json.JSONDecodeError, ValueError):
                pass

        return items

    def _extract_rsc_generic(self, html: str, marker: str) -> list[dict]:
        """Extract arrays from RSC data using a marker field."""
        items: list[dict] = []

        for match in re.finditer(
            r'<script[^>]*>self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>',
            html,
            re.DOTALL,
        ):
            chunk = match.group(1)
            try:
                chunk = json.loads(f'"{chunk}"')
            except (json.JSONDecodeError, ValueError):
                continue

            if marker not in chunk:
                continue

            # Find arrays containing the marker
            for arr_match in re.finditer(
                r"\[(\{[^[\]]*?"
                + re.escape(marker)
                + r"[^[\]]*?\}(?:,\{[^[\]]*?\})*)\]",
                chunk,
            ):
                try:
                    parsed = json.loads(f"[{arr_match.group(1)}]")
                    items.extend(parsed)
                except (json.JSONDecodeError, ValueError):
                    pass

        return items

    async def get_donation_points(self) -> list[dict]:
        html = await self._fetch_page("/")
        return self._extract_rsc_pontos(html)

    async def get_help_requests(self) -> list[dict]:
        html = await self._fetch_page("/pedido-ajuda")
        return self._extract_rsc_generic(html, "descricao")

    async def scrape(self) -> ScraperResult:
        result = self.create_result()
        await self.safe_fetch(result, "donation_points", self.get_donation_points())
        await self.safe_fetch(result, "help_requests", self.get_help_requests())
        return result
