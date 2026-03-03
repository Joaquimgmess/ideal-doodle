import json
import re

from app.scrapers.base import BaseScraper, ScraperResult


def _clean_rsc_json(text: str) -> str:
    """Remove RSC-specific prefixes like $D before dates."""
    return re.sub(r'"\$D(\d{4}-)', r'"\1', text)


class AjudaImediataScraper(BaseScraper):
    portal_id = "12-ajuda-imediata"
    portal_name = "Ajuda Imediata"
    base_url = "https://ajuda-imediata.vercel.app"

    async def get_items(self) -> list[dict]:
        """Extrai itens do HTML renderizado server-side (Next.js RSC)."""
        async with self.get_client() as client:
            response = await client.get(self.base_url)
            response.raise_for_status()

        html = response.text
        items: list[dict] = []

        for match in re.finditer(
            r'<script[^>]*>self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>',
            html,
            re.DOTALL,
        ):
            chunk = match.group(1)
            if "itensIniciais" not in chunk:
                continue

            # Decode JSON string escapes (RSC data is already UTF-8)
            try:
                chunk = json.loads(f'"{chunk}"')
            except (json.JSONDecodeError, ValueError):
                continue

            # Find the itensIniciais array
            idx = chunk.find("itensIniciais")
            arr_start = chunk.find("[", idx)
            if arr_start < 0:
                continue

            # Find matching closing bracket
            depth = 0
            arr_end = arr_start
            for i in range(arr_start, len(chunk)):
                if chunk[i] == "[":
                    depth += 1
                elif chunk[i] == "]":
                    depth -= 1
                if depth == 0:
                    arr_end = i + 1
                    break

            arr_str = _clean_rsc_json(chunk[arr_start:arr_end])

            try:
                parsed = json.loads(arr_str)
                for item in parsed:
                    item.pop("pin_seguranca", None)
                    items.append(item)
            except (json.JSONDecodeError, ValueError):
                pass

        return items

    async def scrape(self) -> ScraperResult:
        result = ScraperResult(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            url=self.base_url,
        )

        try:
            items = await self.get_items()
            ofertas = [i for i in items if i.get("tipo_publicacao") == "OFERTA"]
            pedidos = [i for i in items if i.get("tipo_publicacao") == "PEDIDO"]
            result.data = {
                "items": items,
                "ofertas": len(ofertas),
                "pedidos": len(pedidos),
                "total": len(items),
            }
        except Exception as exc:
            result.errors.append(str(exc))
            result.data = {"items": [], "total": 0}

        return result
