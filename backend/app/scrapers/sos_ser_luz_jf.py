from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ScraperResult


class SosSerLuzJfScraper(BaseScraper):
    portal_id = "11-sos-ser-luz-jf"
    portal_name = "SOS Ser Luz JF"
    base_url = "https://sos-ser-luz-jf.up.railway.app"

    async def get_form_fields(self) -> dict:
        """Extrai os campos do formulário público de pedido de ajuda."""
        async with self.get_client() as client:
            response = await client.get(f"{self.base_url}/help_requests/new")
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.select_one("form")
        if not form:
            return {"available": False, "reason": "Form not found"}

        fields: list[dict] = []
        for inp in form.select("input, textarea, select"):
            name = inp.get("name", "")
            if (
                name
                and not name.startswith("authenticity_token")
                and not name.startswith("utf8")
            ):
                field: dict = {
                    "name": name,
                    "type": inp.get("type", inp.name),
                }
                if inp.name == "select":
                    options = [
                        opt.get_text(strip=True)
                        for opt in inp.select("option")
                        if opt.get("value")
                    ]
                    field["options"] = options
                fields.append(field)

        return {"available": True, "fields": fields}

    async def scrape(self) -> ScraperResult:
        """Scraping limitado - dados ficam atrás de login NGO.
        Apenas extrai a estrutura do formulário público."""
        result = ScraperResult(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            url=self.base_url,
        )

        try:
            form_info = await self.get_form_fields()
            result.data["form_fields"] = form_info
            result.data["note"] = (
                "Dados de pedidos ficam atrás de login em /ngo/help_requests. "
                "Apenas a estrutura do formulário público é acessível."
            )
        except Exception as exc:
            result.errors.append(str(exc))

        return result
