import asyncio
import math

from .base import BaseScraper, ScraperResult

PAGE_LIMIT = 500


class SosMinasGrowberryScraper(BaseScraper):
    portal_id = "05-sos-minas-growberry"
    portal_name = "SOS Minas (Growberry)"
    base_url = "https://sosminas.growberry.com.br"

    async def _fetch_voluntarios_page(self, client, page: int) -> list[dict]:
        r = await client.get(
            f"{self.base_url}/api/voluntarios.php",
            params={"page": page, "limit": PAGE_LIMIT},
        )
        r.raise_for_status()
        return r.json().get("data", [])

    async def get_pedidos(self) -> list[dict]:
        async with self.get_client() as client:
            r = await client.get(f"{self.base_url}/api/pedidos.php")
            r.raise_for_status()
            return r.json()

    async def get_all_voluntarios(self) -> list[dict]:
        async with self.get_client() as client:
            # página 1 traz o total
            r = await client.get(
                f"{self.base_url}/api/voluntarios.php",
                params={"page": 1, "limit": PAGE_LIMIT},
            )
            r.raise_for_status()
            payload = r.json()
            first_page = payload.get("data", [])
            total = payload.get("total", 0)

            n_pages = math.ceil(total / PAGE_LIMIT)
            if n_pages <= 1:
                return first_page

            # demais páginas em paralelo
            rest = await asyncio.gather(
                *[
                    self._fetch_voluntarios_page(client, p)
                    for p in range(2, n_pages + 1)
                ]
            )

        all_items = first_page + [item for page in rest for item in page]
        seen: dict = {}
        for item in all_items:
            seen[item["id"]] = item
        return list(seen.values())

    async def scrape(self) -> ScraperResult:
        result = self.create_result()

        pedidos, all_voluntarios = await asyncio.gather(
            self.get_pedidos(),
            self.get_all_voluntarios(),
            return_exceptions=True,
        )

        if isinstance(pedidos, Exception):
            result.errors.append(f"get_pedidos: {pedidos}")
            pedidos = []

        if isinstance(all_voluntarios, Exception):
            result.errors.append(f"get_all_voluntarios: {all_voluntarios}")
            all_voluntarios = []

        result.data = {
            "pedidos": pedidos,
            "voluntarios": [v for v in all_voluntarios if v.get("tipo") != "doacao"],
            "doacoes": [v for v in all_voluntarios if v.get("tipo") == "doacao"],
        }

        return result
