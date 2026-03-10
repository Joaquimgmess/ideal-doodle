from app.scrapers.base import BaseScraper, ScraperResult

TRPC_URL = "https://interdicoesjf.manus.space/api/trpc/interdicoes.list"


class InterdicoesJfScraper(BaseScraper):
    portal_id = "16-interdicoes-jf"
    portal_name = "Interdições JF"
    base_url = "https://interdicoesjf.manus.space"

    async def get_interdicoes(self) -> list[dict]:
        async with self.get_client() as client:
            response = await client.get(TRPC_URL)
            response.raise_for_status()
            payload = response.json()
            data = payload.get("result", {}).get("data", {}).get("json", {})
            return data.get("data", [])

    async def scrape(self) -> ScraperResult:
        result = self.create_result()

        try:
            interdicoes = await self.get_interdicoes()
            interditadas = [i for i in interdicoes if i.get("Status") == "INTERDITADA"]
            parciais = [
                i for i in interdicoes if i.get("Status") == "PARCIALMENTE LIVRE"
            ]
            livres = [
                i
                for i in interdicoes
                if i.get("Status", "").upper() in ("LIVRE", "LIBERADA", "VIA LIBERADA")
            ]
            result.data = {
                "interdicoes": interdicoes,
                "interditadas": len(interditadas),
                "parcialmente_livres": len(parciais),
                "livres": len(livres),
                "total": len(interdicoes),
            }
        except Exception as exc:
            result.errors.append(str(exc))
            result.data = {"interdicoes": [], "total": 0}

        return result
