from app.scrapers.base import BaseScraper, ScraperResult


class SosJfOrgScraper(BaseScraper):
    portal_id = "06-sosjf-org"
    portal_name = "SOS JF (.org)"
    base_url = "https://sosjf.org"

    async def get_alerts_and_news(self) -> list[dict]:
        async with self.get_client() as client:
            response = await client.get(f"{self.base_url}/api/alerts")
            response.raise_for_status()
            items: list[dict] = response.json()

        for item in items:
            item_id: str = item.get("id", "")
            item["item_type"] = "alert" if item_id.startswith("alert-") else "news"

        return items

    async def get_alerts(self) -> list[dict]:
        items = await self.get_alerts_and_news()
        alerts = [item for item in items if item.get("id", "").startswith("alert-")]
        return sorted(alerts, key=lambda x: x.get("date", ""), reverse=True)

    async def get_news(self) -> list[dict]:
        items = await self.get_alerts_and_news()
        news = [item for item in items if item.get("id", "").startswith("news-")]
        return sorted(news, key=lambda x: x.get("date", ""), reverse=True)

    async def get_reports(self) -> list[dict]:
        async with self.get_client() as client:
            response = await client.get(f"{self.base_url}/api/reports")
            response.raise_for_status()
            reports: list[dict] = response.json()

        return reports if reports else []

    async def _get_alerts_news_split(self) -> dict[str, list[dict]]:
        items = await self.get_alerts_and_news()

        def by_date(x: dict) -> str:
            return x.get("date", "")

        return {
            "alerts": sorted(
                [i for i in items if i.get("id", "").startswith("alert-")],
                key=by_date,
                reverse=True,
            ),
            "news": sorted(
                [i for i in items if i.get("id", "").startswith("news-")],
                key=by_date,
                reverse=True,
            ),
        }

    async def scrape(self) -> ScraperResult:
        result = self.create_result()

        try:
            split = await self._get_alerts_news_split()
            result.data.update(split)
        except Exception as exc:
            result.errors.append(f"alerts_news: {exc}")
            result.data["alerts"] = []
            result.data["news"] = []

        await self.safe_fetch(result, "reports", self.get_reports())
        return result
