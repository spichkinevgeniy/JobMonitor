from aiogram import Router

from app.core.config import config
from app.telegram.bot.routers.account import router as account_router
from app.telegram.bot.routers.broadcast import router as broadcast_router
from app.telegram.bot.routers.help import router as help_router
from app.telegram.bot.routers.onboarding import router as onboarding_router
from app.telegram.bot.routers.profile import router as profile_router
from app.telegram.bot.routers.resume import router as resume_router
from app.telegram.bot.routers.settings import router as settings_router
from app.telegram.bot.routers.vacancy_feedback import router as vacancy_feedback_router


def get_developer_router(environment: str) -> Router | None:
    if environment != "development":
        return None
    from app.telegram.bot.routers.developer import router as developer_router

    return developer_router


def get_router() -> Router:
    router = Router()
    developer_router = get_developer_router(config.APP_ENV)
    if developer_router is not None:
        router.include_router(developer_router)
    router.include_router(onboarding_router)
    router.include_router(broadcast_router)
    router.include_router(settings_router)
    router.include_router(resume_router)
    router.include_router(profile_router)
    router.include_router(vacancy_feedback_router)
    router.include_router(help_router)
    router.include_router(account_router)
    return router
