from fastapi import APIRouter, Request
from sqlmodel import text

from app.api.deps import SessionDep

router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/health-check/")
async def health_check() -> dict[str, bool]:
    """Liveness probe — app está rodando."""
    return {"alive": True}


@router.get("/ready/")
async def readiness_check(
    request: Request, session: SessionDep
) -> dict[str, bool | str]:
    """Readiness probe — DB conectado e scheduler ativo."""
    checks: dict[str, bool | str] = {}

    # DB
    try:
        await session.exec(text("SELECT 1"))
        checks["db"] = True
    except Exception as exc:
        checks["db"] = False
        checks["db_error"] = str(exc)

    # Scheduler
    scheduler = getattr(request.app.state, "scheduler", None)
    checks["scheduler"] = bool(scheduler and scheduler.running)

    return checks
