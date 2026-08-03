from aiogram import Router

from app.telegram.bot.routers.broadcast import router as broadcast_router
from app.telegram.bot.routers.help import router as help_router
from app.telegram.bot.routers.onboarding import router as onboarding_router
from app.telegram.bot.routers.profile import router as profile_router
from app.telegram.bot.routers.resume import router as resume_router
from app.telegram.bot.routers.settings import router as settings_router


def get_router() -> Router:
    router = Router()
    router.include_router(onboarding_router)
    router.include_router(broadcast_router)
    router.include_router(settings_router)
    router.include_router(resume_router)
    router.include_router(profile_router)
    router.include_router(help_router)
    return router
