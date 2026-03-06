import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.workers.scraper_worker import run_all_scrapers

from sqlmodel import Session, select, func
from app.core.db import engine 

from app.models import KPIHistory, Voluntario 
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

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
        hours=1,  
        id="calc_kpi_voluntarios",
        replace_existing=True,
    )

    logger.info("Cron configurado: interval=%dh", settings.SCRAPER_INTERVAL_HOURS)
    return scheduler


async def atualizar_kpi_voluntarios():
    try:
        async with AsyncSession(engine) as session:
            # 1. No SQLAlchemy Async, usamos session.execute()
            statement = select(func.count()).select_from(Voluntario)
            result = await session.execute(statement)
            
            # 2. Pegamos o primeiro valor do resultado (o count)
            total = result.scalar()

            # 3. Cria e salva o registro
            nova_kpi = KPIHistory(nome_kpi="total_voluntarios", valor=total)
            session.add(nova_kpi)
            
            await session.commit()
            logger.info("KPI de voluntários atualizada: %d", total)
            
    except Exception as e:
        # Importante dar rollback se der erro para não travar a conexão
        await session.rollback()
        logger.error("Erro ao processar KPI de voluntários: %s", e)