import httpx

from app.scrapers.base import BaseScraper, ScraperResult


class CidadeQueCuidaScraper(BaseScraper):
    portal_id = "09-cidade-que-cuida"
    portal_name = "Cidade que Cuida"
    base_url = "https://www.cidadequecuida.com.br"

    SUPABASE_URL = "https://ftdlmkfvddazpioikicv.supabase.co"
    ANON_KEY = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ0ZGxta2Z2ZGRhenBpb2lraWN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwMzQ1NDMsImV4cCI6MjA4NzYxMDU0M30"
        ".heJiCOXw_hXy6ZFB1_WEtg7dpGRIUGAsZNAcg2xBZu8"
    )

    def get_client(self) -> httpx.AsyncClient:
        headers = {
            **self.DEFAULT_HEADERS,
            "apikey": self.ANON_KEY,
            "Authorization": f"Bearer {self.ANON_KEY}",
        }
        return httpx.AsyncClient(
            headers=headers,
            timeout=30.0,
            follow_redirects=True,
        )

    async def _fetch_all_listings(
        self, client: httpx.AsyncClient, extra_filter: str = ""
    ) -> list[dict]:
        results: list[dict] = []
        page_size = 100
        start = 0

        while True:
            end = start + page_size - 1
            url = (
                f"{self.SUPABASE_URL}/rest/v1/listings"
                f"?select=*,users(nome,telefone,bairro){extra_filter}"
            )
            response = await client.get(
                url,
                headers={"Range": f"{start}-{end}"},
            )
            response.raise_for_status()
            page = response.json()
            results.extend(page)

            content_range = response.headers.get("content-range", "")
            if "/" in content_range:
                total = content_range.split("/")[-1]
                if total != "*" and int(total) <= end + 1:
                    break
            if len(page) < page_size:
                break

            start += page_size

        return results

    async def get_listings(
        self, tipo: str | None = None, status: str = "publicado"
    ) -> list[dict]:
        async with self.get_client() as client:
            extra_filter = f"&status=eq.{status}"
            if tipo is not None:
                extra_filter += f"&tipo=eq.{tipo}"
            return await self._fetch_all_listings(client, extra_filter)

    async def get_pedidos(self) -> list[dict]:
        return await self.get_listings(tipo="pedido")

    async def get_doacoes(self) -> list[dict]:
        return await self.get_listings(tipo="doacao")

    async def get_voluntarios(self) -> list[dict]:
        return await self.get_listings(tipo="voluntario")

    async def get_entidades(self) -> list[dict]:
        async with self.get_client() as client:
            response = await client.get(
                f"{self.SUPABASE_URL}/rest/v1/entidades?status=eq.aprovado"
            )
            response.raise_for_status()
            return response.json()

    async def get_stats(self) -> dict:
        async with self.get_client() as client:
            response = await client.post(
                f"{self.SUPABASE_URL}/rest/v1/rpc/get_movement_stats",
                json={},
            )
            response.raise_for_status()
            return response.json()

    async def get_parceiros(self) -> list[dict]:
        async with self.get_client() as client:
            response = await client.get(
                f"{self.SUPABASE_URL}/rest/v1/parceiros?ativo=eq.true&order=ordem"
            )
            response.raise_for_status()
            return response.json()

    async def scrape(self) -> ScraperResult:
        result = self.create_result()

        async with self.get_client() as client:
            for tipo, key in [
                ("pedido", "pedidos"),
                ("doacao", "doacoes"),
                ("voluntario", "voluntarios"),
            ]:
                await self.safe_fetch(
                    result,
                    key,
                    self._fetch_all_listings(
                        client, f"&status=eq.publicado&tipo=eq.{tipo}"
                    ),
                )

        await self.safe_fetch(result, "entidades", self.get_entidades())
        await self.safe_fetch(result, "stats", self.get_stats(), default={})

        return result
