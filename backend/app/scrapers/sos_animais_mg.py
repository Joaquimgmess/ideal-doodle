from urllib.parse import quote

import httpx

from app.scrapers.base import BaseScraper, ScraperResult

ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRlcHJxaGJtZHB1eXFodGtwZ2htIiwicm9sZSI6"
    "ImFub24iLCJpYXQiOjE3NzIxNzM4NzQsImV4cCI6MjA4Nzc0OTg3NH0"
    ".IOvBUyHcE7maWivye_G1yutPYOo6qYvxBOyVExb--es"
)

SELECT_FIELDS = (
    "id,post_type,person_name,phone,pet_name,animal_type,"
    "city,location,description,image_url,status,created_at"
)


class SosAnimaisMgScraper(BaseScraper):
    portal_id = "03-sos-animais-mg"
    portal_name = "SOS Animais MG"
    base_url = "https://sosanimaismg.codeheroes.com.br"

    SUPABASE_URL = "https://teprqhbmdpuyqhtkpghm.supabase.co"
    ANON_KEY = ANON_KEY

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

    async def _fetch_posts(
        self, client: httpx.AsyncClient, filters: str = ""
    ) -> list[dict]:
        endpoint = f"{self.SUPABASE_URL}/rest/v1/pets_posts"
        base_params = f"select={SELECT_FIELDS}&order=created_at.desc"
        if filters:
            base_params = f"{base_params}&{filters}"

        results: list[dict] = []
        limit = 100
        offset = 0

        while True:
            url = f"{endpoint}?{base_params}&limit={limit}&offset={offset}"
            response = await client.get(url)
            response.raise_for_status()
            batch: list[dict] = response.json()
            if not batch:
                break
            for post in batch:
                post.pop("cpf", None)
            results.extend(batch)
            if len(batch) < limit:
                break
            offset += limit

        return results

    async def get_all_posts(self) -> list[dict]:
        async with self.get_client() as client:
            return await self._fetch_posts(client)

    async def get_lost_pets(self, city: str | None = None) -> list[dict]:
        filters = "post_type=eq.lost&status=eq.active"
        if city:
            filters += f"&city=eq.{quote(city)}"
        async with self.get_client() as client:
            return await self._fetch_posts(client, filters)

    async def get_found_pets(self, city: str | None = None) -> list[dict]:
        filters = "post_type=eq.found&status=eq.active"
        if city:
            filters += f"&city=eq.{quote(city)}"
        async with self.get_client() as client:
            return await self._fetch_posts(client, filters)

    async def get_adoption_pets(self, city: str | None = None) -> list[dict]:
        filters = "post_type=eq.adoption&status=eq.active"
        if city:
            filters += f"&city=eq.{quote(city)}"
        async with self.get_client() as client:
            return await self._fetch_posts(client, filters)

    async def scrape(self) -> ScraperResult:
        result = self.create_result()
        try:
            async with self.get_client() as client:
                lost = await self._fetch_posts(
                    client, "post_type=eq.lost&status=eq.active"
                )
                found = await self._fetch_posts(
                    client, "post_type=eq.found&status=eq.active"
                )
                adoption = await self._fetch_posts(
                    client, "post_type=eq.adoption&status=eq.active"
                )
            result.data = {
                "lost": lost,
                "found": found,
                "adoption": adoption,
                "total": len(lost) + len(found) + len(adoption),
            }
        except Exception as exc:
            result.errors.append(str(exc))
        return result
