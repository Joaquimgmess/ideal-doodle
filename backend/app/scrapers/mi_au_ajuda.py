import httpx

from app.scrapers.base import BaseScraper, ScraperResult

ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFod3F1YXNkb3djdWhjYWdhaWd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIyOTU2MDIsImV4cCI6MjA4Nzg3MTYwMn0"
    ".4NT3avyqe-hDo8q1ySUeNyKYCy7Xuk2VsF2BGUODP58"
)


class MiAuAjudaScraper(BaseScraper):
    portal_id = "18-mi-au-ajuda"
    portal_name = "Mi Au Ajuda"
    base_url = "https://mi-au-ajuda.lovable.app"

    SUPABASE_URL = "https://qhwquasdowcuhcagaigt.supabase.co"

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
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_acolhedores(self) -> list[dict]:
        async with self.get_client() as client:
            return await self._fetch_table(
                client, "acolhedores", "&ativo=eq.true&order=created_at.desc"
            )

    async def get_pets(self) -> list[dict]:
        async with self.get_client() as client:
            return await self._fetch_table(
                client, "pets", "&status=eq.buscando&order=created_at.desc"
            )

    async def _fetch_clean(
        self, client: httpx.AsyncClient, table: str, params: str
    ) -> list[dict]:
        data = await self._fetch_table(client, table, params)
        for item in data:
            item.pop("token_edicao", None)
        return data

    async def scrape(self) -> ScraperResult:
        result = self.create_result()
        async with self.get_client() as client:
            for table, params, key in [
                ("acolhedores", "&ativo=eq.true&order=created_at.desc", "acolhedores"),
                ("pets", "&status=eq.buscando&order=created_at.desc", "pets"),
            ]:
                await self.safe_fetch(
                    result, key, self._fetch_clean(client, table, params)
                )
        return result
