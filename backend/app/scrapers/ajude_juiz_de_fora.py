import httpx

from app.scrapers.base import BaseScraper, ScraperResult

ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl4Z3B4bHN2Z2Z5emliemtxb2NkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIxMjQ2NzEsImV4cCI6MjA4NzcwMDY3MX0"
    ".2IC4Zgrjs2QFqzP5_bGdvYfRDi6S1-vp1PaMwl0VQYM"
)


class AjudeJuizDeForaScraper(BaseScraper):
    portal_id = "10-ajude-juiz-de-fora"
    portal_name = "Ajude Juiz de Fora"
    base_url = "https://ajudejuizdefora.vercel.app"

    SUPABASE_URL = "https://yxgpxlsvgfyzibzkqocd.supabase.co"

    def get_client(self) -> httpx.AsyncClient:
        headers = {
            **self.DEFAULT_HEADERS,
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}",
        }
        return httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True)

    async def _fetch_table(
        self, client: httpx.AsyncClient, table: str, params: str = ""
    ) -> list[dict]:
        url = f"{self.SUPABASE_URL}/rest/v1/{table}?select=*{params}"
        results: list[dict] = []
        limit = 100
        offset = 0

        while True:
            response = await client.get(
                url, headers={"Range": f"{offset}-{offset + limit - 1}"}
            )
            response.raise_for_status()
            batch: list[dict] = response.json()
            results.extend(batch)
            if len(batch) < limit:
                break
            offset += limit

        return results

    async def get_collection_points(self) -> list[dict]:
        async with self.get_client() as client:
            return await self._fetch_table(
                client, "collection_points", "&order=created_at.desc"
            )

    async def get_needs(self) -> list[dict]:
        async with self.get_client() as client:
            return await self._fetch_table(client, "needs", "&is_active=eq.true")

    async def get_reports(self) -> list[dict]:
        async with self.get_client() as client:
            return await self._fetch_table(client, "reports", "&order=created_at.desc")

    async def scrape(self) -> ScraperResult:
        result = ScraperResult(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            url=self.base_url,
        )

        async with self.get_client() as client:
            for table, params, key in [
                ("collection_points", "&order=created_at.desc", "collection_points"),
                ("needs", "&is_active=eq.true", "needs"),
                ("reports", "&order=created_at.desc", "reports"),
            ]:
                try:
                    result.data[key] = await self._fetch_table(client, table, params)
                except Exception as exc:
                    result.errors.append(f"{key}: {exc}")
                    result.data[key] = []

        return result
