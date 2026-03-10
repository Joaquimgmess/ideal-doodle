import httpx

from app.scrapers.base import BaseScraper, ScraperResult

ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtuZnVwbWFhamtxYnp1b3hnbHNwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIyNDI2NTksImV4cCI6MjA4NzgxODY1OX0"
    ".8LVcp2eRZVTRcO4NNERuaDIRUWYfXZgootK1EimMJ9w"
)


class UnidosPorJfScraper(BaseScraper):
    portal_id = "20-unidos-por-jf"
    portal_name = "Unidos por JF"
    base_url = "https://unidosporjf.com.br"

    SUPABASE_URL = "https://knfupmaajkqbzuoxglsp.supabase.co"

    def get_client(self) -> httpx.AsyncClient:
        headers = {
            **self.DEFAULT_HEADERS,
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}",
        }
        return httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True)

    async def get_help_entries(self, entry_type: str | None = None) -> list[dict]:
        params = "select=*&order=created_at.desc"
        if entry_type:
            params += f"&type=eq.{entry_type}"
        url = f"{self.SUPABASE_URL}/rest/v1/help_entries?{params}"
        async with self.get_client() as client:
            response = await client.get(url)
            response.raise_for_status()
            data: list[dict] = response.json()
            for item in data:
                item.pop("security_token", None)
            return data

    async def get_pedidos(self) -> list[dict]:
        return await self.get_help_entries(entry_type="pedido")

    async def get_voluntarios(self) -> list[dict]:
        return await self.get_help_entries(entry_type="voluntario")

    async def scrape(self) -> ScraperResult:
        result = self.create_result()

        try:
            entries = await self.get_help_entries()
            pedidos = [e for e in entries if e.get("type") == "pedido"]
            voluntarios = [e for e in entries if e.get("type") == "voluntario"]
            result.data = {
                "pedidos": pedidos,
                "voluntarios": voluntarios,
                "total": len(entries),
            }
        except Exception as exc:
            result.errors.append(str(exc))
            result.data = {"pedidos": [], "voluntarios": [], "total": 0}

        return result
