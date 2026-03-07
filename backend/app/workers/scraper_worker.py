import asyncio
import logging
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import engine
from app.models import (
    FeedItem as DBFeedItem,
)
from app.models import (
    Outro as DBOutro,
)
from app.models import (
    Pedido as DBPedido,
)
from app.models import (
    Pet as DBPet,
)
from app.models import (
    PontoAjuda as DBPontoAjuda,
)
from app.models import (
    Voluntario as DBVoluntario,
)
from app.scrapers import (
    AjudaEmjfScraper,
    AjudaImediataScraper,
    AjudaJfArcteiScraper,
    AjudeIoScraper,
    AjudeJfScraper,
    AjudeJuizDeForaScraper,
    CidadeQueCuidaScraper,
    ContaPublicaScraper,
    EmergenciaMgScraper,
    InterdicoesJfScraper,
    MiAuAjudaScraper,
    # MinasEmergenciaScraper,  # usa Playwright — desabilitado temporariamente
    OndeDoarScraper,
    ScraperResult,
    SosAnimaisMgScraper,
    SosJfOnlineScraper,
    SosJfOrgScraper,
    SosMinasGrowberryScraper,
    SosSerLuzJfScraper,
    UnidosPorJfScraper,
    ZonaDaMataAlertasScraper,
)
from app.scrapers.normalizer import normalize_all

logger = logging.getLogger(__name__)

SCRAPERS = [
    EmergenciaMgScraper,
    SosAnimaisMgScraper,
    SosMinasGrowberryScraper,
    SosJfOrgScraper,
    SosJfOnlineScraper,
    AjudeIoScraper,
    CidadeQueCuidaScraper,
    AjudeJuizDeForaScraper,
    SosSerLuzJfScraper,
    AjudaImediataScraper,
    AjudaJfArcteiScraper,
    OndeDoarScraper,
    InterdicoesJfScraper,
    AjudaEmjfScraper,
    MiAuAjudaScraper,
    ZonaDaMataAlertasScraper,
    UnidosPorJfScraper,
    AjudeJfScraper,
    ContaPublicaScraper,
]


async def _run_one(cls) -> ScraperResult:
    scraper = cls()
    try:
        result = await scraper.scrape()
        level = logging.WARNING if result.errors else logging.INFO
        logger.log(
            level, "[%s] done — errors=%d", scraper.portal_name, len(result.errors)
        )
        return result
    except Exception as exc:
        logger.error("[%s] failed: %s", scraper.portal_name, exc)
        return ScraperResult(
            portal_id=scraper.portal_id,
            portal_name=scraper.portal_name,
            url=scraper.base_url,
            errors=[str(exc)],
        )


async def _upsert(
    session: AsyncSession, db_cls: Any, rows: list[dict[str, Any]]
) -> None:
    if not rows:
        return
    # deduplicar por id — portais diferentes podem gerar o mesmo ID
    rows = list({row["id"]: row for row in rows}.values())
    stmt = pg_insert(db_cls).values(rows)
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in db_cls.__table__.columns
        if c.name != "id"
    }
    await session.execute(
        stmt.on_conflict_do_update(index_elements=["id"], set_=update_cols)
    )


async def _persist(
    session: AsyncSession, results: list[ScraperResult]
) -> dict[str, int]:
    normalized = normalize_all(results)

    mapping = [
        (DBPedido, normalized.pedidos, "pedidos"),
        (DBVoluntario, normalized.voluntarios, "voluntarios"),
        (DBPontoAjuda, normalized.pontos, "pontos"),
        (DBPet, normalized.pets, "pets"),
        (DBFeedItem, normalized.feed, "feed"),
        (DBOutro, normalized.outros, "outros"),
    ]

    counts: dict[str, int] = {}
    for db_cls, items, name in mapping:
        rows = [item.model_dump() for item in items]
        await _upsert(session, db_cls, rows)
        counts[name] = len(rows)

    await session.commit()
    return counts


async def run_all_scrapers(batch_size: int = 5) -> list[ScraperResult]:
    logger.info("Scraper worker started (%d portais)", len(SCRAPERS))
    all_results: list[ScraperResult] = []
    batches = [
        SCRAPERS[i : i + batch_size] for i in range(0, len(SCRAPERS), batch_size)
    ]
    for batch in batches:
        batch_results = await asyncio.gather(*[_run_one(cls) for cls in batch])
        all_results.extend(batch_results)

    ok = sum(1 for r in all_results if not r.errors)
    logger.info("Scraper worker done: %d/%d OK", ok, len(all_results))

    async with AsyncSession(engine) as session:
        counts = await _persist(session, all_results)

    total = sum(counts.values())
    logger.info(
        "Persisted %d items — %s",
        total,
        " | ".join(f"{k}={v}" for k, v in counts.items()),
    )
    return all_results
