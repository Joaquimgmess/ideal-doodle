from typing import Any

import httpx

from app.scrapers.base import BaseScraper, ScraperResult

HARDCODED_SHELTERS = [
    {
        "name": "E. M. Vereador Raymundo Hargreaves",
        "neighborhood": "Bom Jardim",
        "lat": -21.7341289,
        "lng": -43.3347358,
    },
    {
        "name": "E.M. Aurea Bicalho",
        "neighborhood": "Linhares",
        "lat": -21.7346721,
        "lng": -43.3327744,
    },
    {
        "name": "E.M. Professora Marlene Barros",
        "neighborhood": "Marumbi",
        "lat": -21.7309203,
        "lng": -43.3389344,
    },
    {
        "name": "E.M. Murilo Mendes",
        "neighborhood": "Grajau",
        "lat": -21.7452094,
        "lng": -43.3456885,
    },
    {
        "name": "E.M. Dilermando Cruz",
        "neighborhood": "Vila Ideal",
        "lat": -21.7789343,
        "lng": -43.3309,
    },
    {
        "name": "E.M. Belmira Duarte Dias",
        "neighborhood": "JK",
        "lat": -21.72081,
        "lng": -43.3327459,
    },
    {
        "name": "E.M. Professor Irineu Guimaraes",
        "neighborhood": "Sao Benedito",
        "lat": -21.7513358,
        "lng": -43.3282428,
    },
    {
        "name": "E.M. Dante Jaime Brochado",
        "neighborhood": "Santo Antonio",
        "lat": -21.772862,
        "lng": -43.3150169,
    },
    {
        "name": "E.M. Gabriel Goncalves da Silva",
        "neighborhood": "Ipiranga",
        "lat": -21.7954852,
        "lng": -43.3549871,
    },
    {
        "name": "E.M. Fernao Dias Paes",
        "neighborhood": "Bandeirantes",
        "lat": -21.720762,
        "lng": -43.3561579,
    },
    {
        "name": "E. M. Doutor Adhemar Rezende de Andrade",
        "neighborhood": "Sao Pedro",
        "lat": -21.7717837,
        "lng": -43.3911361,
    },
    {
        "name": "E.M. Henrique Jose de Souza",
        "neighborhood": "Cidade do Sol",
        "lat": -21.7177581,
        "lng": -43.4126828,
    },
    {
        "name": "E.M. Professor Nilo Camilo Ayupe",
        "neighborhood": "Paineiras",
        "lat": -21.7683296,
        "lng": -43.3584676,
    },
    {
        "name": "E. M. Professor Paulo Rogerio dos Santos",
        "neighborhood": "Monte Castelo",
        "lat": -21.7444369,
        "lng": -43.3867951,
    },
    {
        "name": "E.M. Doutor Paulo Japyassu Coelho",
        "neighborhood": "Parque Guarani",
        "lat": -21.71447,
        "lng": -43.35389,
    },
]

FIRESTORE_BASE_URL = "https://firestore.googleapis.com/v1/projects/ajude-io/databases/(default)/documents"


class AjudeIoScraper(BaseScraper):
    portal_id = "08-ajude-io"
    portal_name = "Ajude.io"
    base_url = "https://ajude.io/"

    def _parse_field(self, field: dict) -> Any:
        if "stringValue" in field:
            return field["stringValue"]
        if "integerValue" in field:
            return int(field["integerValue"])
        if "doubleValue" in field:
            return field["doubleValue"]
        if "booleanValue" in field:
            return field["booleanValue"]
        if "timestampValue" in field:
            return field["timestampValue"]
        if "nullValue" in field:
            return None
        if "geoPointValue" in field:
            return {
                "lat": field["geoPointValue"]["latitude"],
                "lng": field["geoPointValue"]["longitude"],
            }
        if "arrayValue" in field:
            return [self._parse_field(v) for v in field["arrayValue"].get("values", [])]
        if "mapValue" in field:
            return {
                k: self._parse_field(v)
                for k, v in field["mapValue"].get("fields", {}).items()
            }
        return field

    def _parse_doc(self, doc: dict) -> dict:
        doc_id = doc["name"].split("/")[-1]
        parsed: dict[str, Any] = {"id": doc_id}
        for key, value in doc.get("fields", {}).items():
            parsed[key] = self._parse_field(value)
        return parsed

    async def _fetch_collection(
        self,
        client: httpx.AsyncClient,
        collection: str,
        page_size: int = 300,
    ) -> list[dict]:
        url = f"{FIRESTORE_BASE_URL}/{collection}"
        params: dict[str, Any] = {"pageSize": page_size}
        documents: list[dict] = []

        while True:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

            for doc in payload.get("documents", []):
                documents.append(self._parse_doc(doc))

            next_page_token = payload.get("nextPageToken")
            if not next_page_token:
                break
            params["pageToken"] = next_page_token

        return documents

    async def get_help_requests(self) -> list[dict]:
        async with self.get_client() as client:
            return await self._fetch_collection(client, "help_requests", page_size=300)

    async def get_volunteer_offers(self) -> list[dict]:
        async with self.get_client() as client:
            return await self._fetch_collection(
                client, "volunteer_offers", page_size=300
            )

    async def get_donation_points(self) -> list[dict]:
        async with self.get_client() as client:
            return await self._fetch_collection(
                client, "donation_points", page_size=100
            )

    async def get_shelters(self) -> list[dict]:
        return HARDCODED_SHELTERS

    async def scrape(self) -> ScraperResult:
        result = ScraperResult(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            url=self.base_url,
        )

        async with self.get_client() as client:
            for collection, page_size, key in [
                ("help_requests", 300, "help_requests"),
                ("volunteer_offers", 300, "volunteer_offers"),
                ("donation_points", 100, "donation_points"),
            ]:
                try:
                    result.data[key] = await self._fetch_collection(
                        client, collection, page_size=page_size
                    )
                except Exception as exc:
                    result.errors.append(f"{key}: {exc}")
                    result.data[key] = []

        result.data["shelters"] = HARDCODED_SHELTERS

        return result
