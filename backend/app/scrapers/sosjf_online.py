from app.scrapers.base import BaseScraper, ScraperResult

API_URL = "https://v1.sos-jf.workers.dev/"


class SosJfOnlineScraper(BaseScraper):
    portal_id = "07-sosjf-online"
    portal_name = "SOS JF (.online)"
    base_url = "https://www.sos-jf.online/"

    async def get_all_pontos(self) -> list[dict]:
        async with self.get_client() as client:
            response = await client.get(API_URL)
            response.raise_for_status()
            return response.json()

    async def get_collection_points(self) -> list[dict]:
        pontos = await self.get_all_pontos()
        return [p for p in pontos if p.get("type") == "coleta"]

    async def get_shelters(self) -> list[dict]:
        pontos = await self.get_all_pontos()
        return [p for p in pontos if p.get("type") == "abrigo"]

    async def get_ponto_by_neighborhood(self, neighborhood: str) -> list[dict]:
        pontos = await self.get_all_pontos()
        needle = neighborhood.lower()
        return [p for p in pontos if p.get("neighborhood", "").lower() == needle]

    async def scrape(self) -> ScraperResult:
        result = self.create_result()
        try:
            async with self.get_client() as client:
                response = await client.get(API_URL)
                response.raise_for_status()
                pontos: list[dict] = response.json()

            collection_points = [p for p in pontos if p.get("type") == "coleta"]
            shelters = [p for p in pontos if p.get("type") == "abrigo"]

            result.data = {
                "collection_points": collection_points,
                "shelters": shelters,
                "total": len(pontos),
            }
        except Exception as exc:
            result.errors.append(str(exc))

        return result
