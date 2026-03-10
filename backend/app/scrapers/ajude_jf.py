import httpx

from app.scrapers.base import BaseScraper, ScraperResult

ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpkcGxvbGx4dmZzYmV4cmhqZnpuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIxNDQ0NjUsImV4cCI6MjA4NzcyMDQ2NX0"
    ".6FDbF3e9FL-WG_tXHlRXg_OP2K_T2TN-nXIVQcyvSPo"
)

TABLES_WITH_CREATED_AT = [
    "pets_perdidos_public",
    "voluntarios_public",
    "lares_temporarios_public",
    "doadores_public",
    "ongs_protetores",
    "pontos_doacao",
    "pontos_alimentacao",
    "abrigos",
    "vaquinhas",
    "adocao",
]

TABLES_WITHOUT_CREATED_AT = [
    "cidades",
]


class AjudeJfScraper(BaseScraper):
    portal_id = "21-ajude-jf"
    portal_name = "Ajude JF (.com.br)"
    base_url = "https://ajudejf.com.br"

    SUPABASE_URL = "https://jdplollxvfsbexrhjfzn.supabase.co"

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

    async def scrape(self) -> ScraperResult:
        result = self.create_result()

        async with self.get_client() as client:
            for table in TABLES_WITH_CREATED_AT:
                await self.safe_fetch(
                    result,
                    table,
                    self._fetch_table(client, table, "&order=created_at.desc"),
                )
            for table in TABLES_WITHOUT_CREATED_AT:
                await self.safe_fetch(result, table, self._fetch_table(client, table))

        return result
