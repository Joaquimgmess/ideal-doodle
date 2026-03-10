"""
Normaliza ScraperResult bruto → NormalizedResult com schema unificado.

Cada portal tem seu módulo em normalizers/<portal>.py com uma função normalize().
O registry mapeia portal_id → função de normalização.
"""

from collections.abc import Callable

from app.schemas.normalized import NormalizedResult
from app.scrapers.base import ScraperResult
from app.scrapers.normalizers import (
    ajuda_emjf,
    ajuda_imediata,
    ajuda_jf_arctei,
    ajude_io,
    ajude_jf,
    ajude_juiz_de_fora,
    cidade_que_cuida,
    conta_publica,
    emergencia_mg,
    interdicoes_jf,
    mi_au_ajuda,
    minas_emergencia,
    onde_doar,
    sos_animais_mg,
    sos_minas_growberry,
    sos_ser_luz_jf,
    sosjf_online,
    sosjf_org,
    unidos_por_jf,
    zona_da_mata_alertas,
)

NORMALIZERS: dict[str, Callable[[ScraperResult], NormalizedResult]] = {
    "01-emergencia-mg": emergencia_mg.normalize,
    "02-minas-emergencia": minas_emergencia.normalize,
    "03-sos-animais-mg": sos_animais_mg.normalize,
    "05-sos-minas-growberry": sos_minas_growberry.normalize,
    "06-sosjf-org": sosjf_org.normalize,
    "07-sosjf-online": sosjf_online.normalize,
    "08-ajude-io": ajude_io.normalize,
    "09-cidade-que-cuida": cidade_que_cuida.normalize,
    "10-ajude-juiz-de-fora": ajude_juiz_de_fora.normalize,
    "11-sos-ser-luz-jf": sos_ser_luz_jf.normalize,
    "12-ajuda-imediata": ajuda_imediata.normalize,
    "13-ajuda-jf-arctei": ajuda_jf_arctei.normalize,
    "15-onde-doar": onde_doar.normalize,
    "16-interdicoes-jf": interdicoes_jf.normalize,
    "17-ajuda-emjf": ajuda_emjf.normalize,
    "18-mi-au-ajuda": mi_au_ajuda.normalize,
    "19-zona-da-mata-alertas": zona_da_mata_alertas.normalize,
    "20-unidos-por-jf": unidos_por_jf.normalize,
    "21-ajude-jf": ajude_jf.normalize,
    "22-conta-publica": conta_publica.normalize,
}


def normalize(result: ScraperResult) -> NormalizedResult:
    fn = NORMALIZERS.get(result.portal_id)
    if fn is None:
        return NormalizedResult()
    return fn(result)


def normalize_all(results: list[ScraperResult]) -> NormalizedResult:
    combined = NormalizedResult()
    for r in results:
        nr = normalize(r)
        combined.pedidos.extend(nr.pedidos)
        combined.voluntarios.extend(nr.voluntarios)
        combined.pontos.extend(nr.pontos)
        combined.pets.extend(nr.pets)
        combined.feed.extend(nr.feed)
        combined.outros.extend(nr.outros)
    return combined
