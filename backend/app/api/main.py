from fastapi import APIRouter

from app.api.routes import (
    api_keys,
    data,
    kpis,
    login,
    private,
    robo_whatsapp,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(data.router)
api_router.include_router(api_keys.router)
api_router.include_router(kpis.router)
api_router.include_router(robo_whatsapp.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
