"""Testes unitários para o normalizer."""

import hashlib
from datetime import datetime, timezone

import pytest

from app.scrapers.base import ScraperResult
from app.scrapers.normalizers import normalize, normalize_all
from app.scrapers.normalizers.helpers import city_slug, first, geo

pytestmark = pytest.mark.anyio

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _result(portal_id: str, data: dict) -> ScraperResult:
    return ScraperResult(
        portal_id=portal_id,
        portal_name=f"Portal {portal_id}",
        url=f"https://{portal_id}.example.com",
        scraped_at=NOW,
        data=data,
    )


# ---------------------------------------------------------------------------
# Helper: _first
# ---------------------------------------------------------------------------


class TestFirst:
    def test_returns_first_non_none(self):
        d = {"a": None, "b": "", "c": "found"}
        assert first(d, "a", "b", "c") == "found"

    def test_returns_default_when_all_empty(self):
        d = {"a": None, "b": ""}
        assert first(d, "a", "b", default="fallback") == "fallback"

    def test_returns_default_for_missing_keys(self):
        assert first({}, "x", "y", default=42) == 42

    def test_returns_zero_as_valid_value(self):
        assert first({"a": 0}, "a") == 0

    def test_returns_false_as_valid_value(self):
        assert first({"a": False}, "a") is False


# ---------------------------------------------------------------------------
# Helper: _geo
# ---------------------------------------------------------------------------


class TestGeo:
    def test_valid_floats(self):
        d = {"lat": -21.76, "lng": -43.35}
        assert geo(d) == (-21.76, -43.35)

    def test_string_floats(self):
        d = {"latitude": "-21.76", "longitude": "-43.35"}
        assert geo(d) == (-21.76, -43.35)

    def test_missing_returns_none(self):
        assert geo({}) == (None, None)

    def test_invalid_returns_none(self):
        d = {"lat": "abc", "lng": "def"}
        assert geo(d) == (None, None)

    def test_partial_valid(self):
        d = {"lat": "-21.76"}
        lat, lng = geo(d)
        assert lat == -21.76
        assert lng is None


# ---------------------------------------------------------------------------
# Helper: _city_slug
# ---------------------------------------------------------------------------


class TestCitySlug:
    def test_normal_city(self):
        d = {"cidade": "Juiz de Fora"}
        assert city_slug(d, "cidade") == "juiz_de_fora"

    def test_fallback(self):
        assert city_slug({}, "cidade") == "mg"

    def test_custom_fallback(self):
        assert city_slug({}, "cidade", fallback="rj") == "rj"


# ---------------------------------------------------------------------------
# normalize() — dispatcher
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_unknown_portal_returns_empty(self):
        result = _result("unknown-portal-xyz", {"stuff": [1, 2, 3]})
        nr = normalize(result)
        assert nr.pedidos == []
        assert nr.voluntarios == []
        assert nr.pontos == []
        assert nr.pets == []
        assert nr.feed == []
        assert nr.outros == []

    def test_emergencia_mg_contacts(self):
        data = {
            "emergency_contacts": [
                {"nome": "Bombeiros", "telefone": "193"},
                {"nome": "SAMU", "telefone": "192"},
            ]
        }
        nr = normalize(_result("01-emergencia-mg", data))
        assert len(nr.outros) == 2
        assert nr.outros[0].tipo == "contato_emergencia"
        assert nr.outros[0].titulo == "Bombeiros"
        assert nr.outros[0].contato == "193"
        assert nr.outros[0].portal_id == "01-emergencia-mg"

    def test_emergencia_mg_id_format(self):
        data = {"emergency_contacts": [{"nome": "Bombeiros", "telefone": "193"}]}
        nr = normalize(_result("01-emergencia-mg", data))
        item = nr.outros[0]
        expected_hash = hashlib.md5(b"Bombeiros193").hexdigest()[:8]
        assert item.id == f"01-emergencia-mg:jf:contato:{expected_hash}"

    def test_emergencia_mg_animal_shelters(self):
        data = {
            "animal_shelters": [
                {
                    "nome": "Abrigo Animal JF",
                    "telefone": "32999999999",
                    "animais": ["cachorro", "gato"],
                    "lat": -21.76,
                    "lng": -43.35,
                }
            ]
        }
        nr = normalize(_result("01-emergencia-mg", data))
        assert len(nr.pontos) == 1
        ponto = nr.pontos[0]
        assert ponto.tipo == "abrigo_animal"
        assert ponto.nome == "Abrigo Animal JF"
        assert ponto.lat == -21.76
        assert ponto.itens == ["cachorro", "gato"]

    def test_emergencia_mg_volunteers(self):
        data = {"transport_volunteers": [{"nome": "João", "telefone": "32988887777"}]}
        nr = normalize(_result("01-emergencia-mg", data))
        assert len(nr.voluntarios) == 1
        assert nr.voluntarios[0].categoria == "transporte"
        assert nr.voluntarios[0].nome == "João"

    def test_emergencia_mg_help_links(self):
        data = {
            "help_links": [
                {"titulo": "Doações", "url": "https://example.com", "descricao": "Doe"}
            ]
        }
        nr = normalize(_result("01-emergencia-mg", data))
        assert len(nr.outros) == 1
        assert nr.outros[0].tipo == "link"
        assert nr.outros[0].url == "https://example.com"

    def test_sos_animais_mg_pets(self):
        data = {
            "lost": [
                {
                    "id": "pet-1",
                    "pet_name": "Rex",
                    "animal_type": "cachorro",
                    "description": "Perdido no centro",
                    "phone": "32999999999",
                    "city": "Juiz de Fora",
                }
            ],
            "found": [
                {
                    "id": "pet-2",
                    "pet_name": "Mia",
                    "animal_type": "gato",
                    "city": "Juiz de Fora",
                }
            ],
        }
        nr = normalize(_result("03-sos-animais-mg", data))
        assert len(nr.pets) == 2
        lost = nr.pets[0]
        assert lost.tipo == "perdido"
        assert lost.nome == "Rex"
        assert lost.id == "03-sos-animais-mg:juiz_de_fora:pet-1"
        found = nr.pets[1]
        assert found.tipo == "encontrado"
        assert found.nome == "Mia"

    def test_empty_data_returns_empty_result(self):
        nr = normalize(_result("01-emergencia-mg", {}))
        assert nr.pedidos == []
        assert nr.outros == []


# ---------------------------------------------------------------------------
# normalize_all()
# ---------------------------------------------------------------------------


class TestNormalizeAll:
    def test_combines_multiple_results(self):
        r1 = _result(
            "01-emergencia-mg",
            {"emergency_contacts": [{"nome": "Bombeiros", "telefone": "193"}]},
        )
        r2 = _result(
            "03-sos-animais-mg",
            {
                "lost": [
                    {
                        "id": "p1",
                        "pet_name": "Rex",
                        "animal_type": "cachorro",
                        "city": "JF",
                    }
                ]
            },
        )
        combined = normalize_all([r1, r2])
        assert len(combined.outros) == 1
        assert len(combined.pets) == 1

    def test_empty_list_returns_empty(self):
        combined = normalize_all([])
        assert combined.pedidos == []

    def test_unknown_portals_ignored(self):
        r = _result("portal-que-nao-existe", {"data": [1, 2]})
        combined = normalize_all([r])
        assert combined.pedidos == []
        assert combined.outros == []
