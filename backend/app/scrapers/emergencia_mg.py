from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ScraperResult


class EmergenciaMgScraper(BaseScraper):
    portal_id = "01-emergencia-mg"
    portal_name = "Emergência MG"
    base_url = "https://emergencia-mg.netlify.app"

    async def get_emergency_contacts(self) -> list[dict]:
        return [
            {"nome": "Bombeiros", "telefone": "193"},
            {"nome": "SAMU", "telefone": "192"},
            {"nome": "Defesa Civil", "telefone": "199"},
            {"nome": "PM", "telefone": "190"},
            {"nome": "CVV", "telefone": "188"},
        ]

    async def get_help_links(self) -> list[dict]:
        results: list[dict] = []
        try:
            async with self.get_client() as client:
                response = await client.get(self.base_url)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            current_section: str | None = None

            for element in soup.select(".section .section-label, .link-card"):
                if "section-label" in element.get("class", []):
                    current_section = element.get_text(strip=True)
                    continue

                if "link-card" in element.get("class", []):
                    title_el = element.select_one(".card-title")
                    desc_el = element.select_one(".card-desc")
                    titulo = (
                        "".join(title_el.find_all(string=True, recursive=False)).strip()
                        if title_el
                        else None
                    )
                    results.append(
                        {
                            "titulo": titulo
                            or (title_el.get_text(strip=True) if title_el else None),
                            "descricao": desc_el.get_text(strip=True)
                            if desc_el
                            else None,
                            "url": element.get("href"),
                            "urgente": "urgent" in element.get("class", []),
                            "secao": current_section,
                        }
                    )
        except Exception as exc:
            raise RuntimeError(f"get_help_links: {exc}") from exc

        return results

    async def get_animal_shelters(self) -> list[dict]:
        results: list[dict] = []
        try:
            async with self.get_client() as client:
                response = await client.get(f"{self.base_url}/lares-temporarios")
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for card in soup.select(".contact-card.lar"):
                title_el = card.select_one(".card-title")
                desc_el = card.select_one(".card-desc")
                size_el = card.select_one(".tag.tag-size")
                whatsapp_el = card.select_one("a[href]")

                animais: list[str] = []
                if card.select_one(".tag.tag-cat"):
                    animais.append("gato")
                if card.select_one(".tag.tag-dog"):
                    animais.append("cachorro")

                results.append(
                    {
                        "nome": title_el.get_text(strip=True) if title_el else None,
                        "animais": animais,
                        "porte": size_el.get_text(strip=True) if size_el else None,
                        "telefone": desc_el.get_text(strip=True) if desc_el else None,
                        "whatsapp_url": whatsapp_el.get("href")
                        if whatsapp_el
                        else None,
                    }
                )
        except Exception as exc:
            raise RuntimeError(f"get_animal_shelters: {exc}") from exc

        return results

    async def get_transport_volunteers(self) -> list[dict]:
        results: list[dict] = []
        try:
            async with self.get_client() as client:
                response = await client.get(f"{self.base_url}/lares-temporarios")
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for card in soup.select(".contact-card.transporte"):
                title_el = card.select_one(".card-title")
                desc_el = card.select_one(".card-desc")
                whatsapp_el = card.select_one("a[href]")

                results.append(
                    {
                        "nome": title_el.get_text(strip=True) if title_el else None,
                        "telefone": desc_el.get_text(strip=True) if desc_el else None,
                        "whatsapp_url": whatsapp_el.get("href")
                        if whatsapp_el
                        else None,
                    }
                )
        except Exception as exc:
            raise RuntimeError(f"get_transport_volunteers: {exc}") from exc

        return results

    async def scrape(self) -> ScraperResult:
        result = ScraperResult(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            url=self.base_url,
        )

        for method, key in [
            (self.get_emergency_contacts, "emergency_contacts"),
            (self.get_help_links, "help_links"),
            (self.get_animal_shelters, "animal_shelters"),
            (self.get_transport_volunteers, "transport_volunteers"),
        ]:
            try:
                result.data[key] = await method()
            except Exception as exc:
                result.errors.append(str(exc))
                result.data[key] = []

        return result
