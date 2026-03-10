import httpx

from app.scrapers.base import BaseScraper, ScraperResult

ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkdGNnZ3dzZGpuZ2ZqanZ0dXJiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIxMzI1MTEsImV4cCI6MjA4NzcwODUxMX0"
    ".BTNBiZBOLtz9JHgFD7Tm_DjeY79kt_J-gIApuX-zK7k"
)


class ZonaDaMataAlertasScraper(BaseScraper):
    portal_id = "19-zona-da-mata-alertas"
    portal_name = "Zona da Mata Alertas"
    base_url = "https://zona-da-mata-alertas.vercel.app"

    SUPABASE_URL = "https://fdtcggwsdjngfjjvturb.supabase.co"

    def get_client(self) -> httpx.AsyncClient:
        headers = {
            **self.DEFAULT_HEADERS,
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}",
        }
        return httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True)

    async def get_alerts(self, alert_type: str | None = None) -> list[dict]:
        params = "select=*&order=created_at.desc"
        if alert_type:
            params += f"&type=eq.{alert_type}"
        url = f"{self.SUPABASE_URL}/rest/v1/alerts?{params}"
        async with self.get_client() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def scrape(self) -> ScraperResult:
        result = self.create_result()

        try:
            alerts = await self.get_alerts()
            result.data = {
                "alerts": alerts,
                "total": len(alerts),
            }
        except Exception as exc:
            result.errors.append(str(exc))
            result.data = {"alerts": [], "total": 0}

        return result
