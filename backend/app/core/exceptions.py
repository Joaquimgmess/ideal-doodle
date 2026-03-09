"""Hierarquia de exceções do SOS-JF."""


class SosJFError(Exception):
    """Erro base do projeto."""


# ---------------------------------------------------------------------------
# Scrapers
# ---------------------------------------------------------------------------


class ScraperError(SosJFError):
    """Erro genérico de scraping."""

    def __init__(self, portal_id: str, message: str) -> None:
        self.portal_id = portal_id
        super().__init__(f"[{portal_id}] {message}")


class ScraperHTTPError(ScraperError):
    """Erro HTTP ao acessar portal (4xx, 5xx, connection refused)."""

    def __init__(
        self, portal_id: str, message: str, status_code: int | None = None
    ) -> None:
        self.status_code = status_code
        super().__init__(portal_id, message)


class ScraperTimeoutError(ScraperError):
    """Timeout ao acessar portal."""


class ScraperParseError(ScraperError):
    """Erro ao parsear HTML/JSON do portal."""


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------


class DataValidationError(SosJFError):
    """Erro de validação de dados durante normalização ou persistência."""
