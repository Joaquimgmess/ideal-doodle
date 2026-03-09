import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.config import settings
from app.core.db import engine
from app.models import KPIHistory, Voluntario
from app.workers.scraper_worker import run_all_scrapers

logger = logging.getLogger(__name__)


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        run_all_scrapers,
        trigger="interval",
        hours=settings.SCRAPER_INTERVAL_HOURS,
        id="scraper_all_portals",
        replace_existing=True,
    )

    scheduler.add_job(
        atualizar_kpi_voluntarios,
        trigger="interval",
        hours=settings.KPIS_INTERVAL_HOURS,
        id="calc_kpi_voluntarios",
        replace_existing=True,
    )

    logger.info("Cron configurado: interval=%dh", settings.SCRAPER_INTERVAL_HOURS)
    return scheduler


async def atualizar_kpi_voluntarios():
        async with AsyncSession(engine) as session:
            try:
                statement = select(func.count()).select_from(Voluntario)
                result = await session.execute(statement)
                total = result.scalar()

                nova_kpi = KPIHistory(nome_kpi="total_voluntarios", valor=total)
                session.add(nova_kpi)

                await session.commit()
                logger.info("KPI de voluntários atualizada: %d", total)

            #Correção: Adicionado tratamento de exceção para garantir rollback dentro do bloco
            except Exception as e:
                await session.rollback()
                logger.error("Erro ao processar KPI de voluntários: %s", e)
                raise

