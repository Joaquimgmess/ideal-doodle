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

    async def scrape(self) -> ScraperResult:
        result = ScraperResult(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            url=self.base_url,
        )

        try:
            items = await self.get_alerts_and_news()
            result.data["alerts"] = sorted(
                [i for i in items if i.get("id", "").startswith("alert-")],
                key=lambda x: x.get("date", ""), reverse=True,
            )
            result.data["news"] = sorted(
                [i for i in items if i.get("id", "").startswith("news-")],
                key=lambda x: x.get("date", ""), reverse=True,
            )
        except Exception as exc:
            result.errors.append(f"alerts_news: {exc}")
            result.data["alerts"] = []
            result.data["news"] = []

        try:
            reports = await self.get_reports()
            result.data["reports"] = reports
        except Exception as exc:
            result.errors.append(f"reports: {exc}")
            result.data["reports"] = []

        return result
