import json
import re

from app.scrapers.base import BaseScraper, ScraperResult


def _js_literal_to_json(text: str) -> str:
    """Convert JS object literal to valid JSON (add quotes to keys)."""
    # Add quotes around unquoted keys: {id:1,name:"x"} -> {"id":1,"name":"x"}
    return re.sub(r"(?<=[{,])(\w+)(?=:)", r'"\1"', text)


class AjudaEmjfScraper(BaseScraper):
    portal_id = "17-ajuda-emjf"
    portal_name = "Ajuda EMJF"
    base_url = "https://ajuda.emjf.com.br"

    async def _fetch_bundle(self) -> str:
        async with self.get_client() as client:
            response = await client.get(self.base_url)
            response.raise_for_status()
            html = response.text

            match = re.search(r'src="(/assets/index-[^"]+\.js)"', html)
            if not match:
                raise RuntimeError("Bundle JS not found in HTML")

            bundle_url = f"{self.base_url}{match.group(1)}"
            bundle_response = await client.get(bundle_url)
            bundle_response.raise_for_status()
            return bundle_response.text

    def _extract_arrays(self, js: str) -> dict:
        data: dict = {"collection_points": [], "shelters": [], "pix_keys": []}

        # Shelters: [{id:100,pointType:"shelter",name:"...",... }]
        shelter_match = re.search(r'\[(\{id:\d+,pointType:"shelter".*?\})\]', js)
        if shelter_match:
            try:
                json_str = _js_literal_to_json(shelter_match.group(0))
                data["shelters"] = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass

        # Collection points: [{id:N,name:"...",city:"...",address:"...",lat:...,lng:...,items:[...],hours:"..."}]
        # These DON'T have pointType
        cp_match = re.search(
            r'\[(\{id:\d+,name:"[^"]+",city:"[^"]+",address:"[^"]+"'
            r',lat:-?\d+[\d.]*,lng:-?\d+[\d.]*,items:\[.*?\],hours:"[^"]*"\}(?:,\{.*?\})*)\]',
            js,
        )
        if cp_match:
            try:
                json_str = _js_literal_to_json(cp_match.group(0))
                arr = json.loads(json_str)
                # Filter out shelters that might have been caught
                data["collection_points"] = [
                    p for p in arr if p.get("pointType") != "shelter"
                ]
            except (json.JSONDecodeError, ValueError):
                pass

        # PIX keys: [{id:N,name:"...",pixKey:"...",keyType:"...",holder:"..."}]
        pix_match = re.search(
            r'\[(\{id:\d+,name:"[^"]+",description:"[^"]*",pixKey:"[^"]+".*?\})\]',
            js,
        )
        if pix_match:
            try:
                json_str = _js_literal_to_json(pix_match.group(0))
                data["pix_keys"] = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass

        return data

    async def get_all_data(self) -> dict:
        bundle = await self._fetch_bundle()
        return self._extract_arrays(bundle)

    async def scrape(self) -> ScraperResult:
        result = ScraperResult(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            url=self.base_url,
        )

        try:
            data = await self.get_all_data()
            result.data = data
        except Exception as exc:
            result.errors.append(str(exc))
            result.data = {"collection_points": [], "shelters": [], "pix_keys": []}

        return result
