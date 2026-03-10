from app.scrapers.ajuda_emjf import AjudaEmjfScraper
from app.scrapers.ajuda_imediata import AjudaImediataScraper
from app.scrapers.ajuda_jf_arctei import AjudaJfArcteiScraper
from app.scrapers.ajude_io import AjudeIoScraper
from app.scrapers.ajude_jf import AjudeJfScraper
from app.scrapers.ajude_juiz_de_fora import AjudeJuizDeForaScraper
from app.scrapers.base import BaseScraper, ScraperResult, ScraperStatus
from app.scrapers.cidade_que_cuida import CidadeQueCuidaScraper
from app.scrapers.conta_publica import ContaPublicaScraper
from app.scrapers.emergencia_mg import EmergenciaMgScraper
from app.scrapers.interdicoes_jf import InterdicoesJfScraper
from app.scrapers.mi_au_ajuda import MiAuAjudaScraper
from app.scrapers.onde_doar import OndeDoarScraper
from app.scrapers.sos_animais_mg import SosAnimaisMgScraper
from app.scrapers.sos_minas_growberry import SosMinasGrowberryScraper
from app.scrapers.sos_ser_luz_jf import SosSerLuzJfScraper
from app.scrapers.sosjf_online import SosJfOnlineScraper
from app.scrapers.sosjf_org import SosJfOrgScraper
from app.scrapers.unidos_por_jf import UnidosPorJfScraper
from app.scrapers.zona_da_mata_alertas import ZonaDaMataAlertasScraper

__all__ = [
    "BaseScraper",
    "ScraperResult",
    "ScraperStatus",
    "EmergenciaMgScraper",
    "SosAnimaisMgScraper",
    "SosMinasGrowberryScraper",
    "SosJfOrgScraper",
    "SosJfOnlineScraper",
    "AjudeIoScraper",
    "CidadeQueCuidaScraper",
    "AjudeJuizDeForaScraper",
    "SosSerLuzJfScraper",
    "AjudaImediataScraper",
    "AjudaJfArcteiScraper",
    "OndeDoarScraper",
    "InterdicoesJfScraper",
    "AjudaEmjfScraper",
    "MiAuAjudaScraper",
    "ZonaDaMataAlertasScraper",
    "UnidosPorJfScraper",
    "AjudeJfScraper",
    "ContaPublicaScraper",
]
