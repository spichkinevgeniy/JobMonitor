from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.application.services.export_service import ExportService
from app.application.services.onboarding_service import OnboardingService
from app.application.services.resume_import_service import ResumeImportService
from app.application.services.search_profile_service import SearchProfileService
from app.application.services.stats_service import StatsService
from app.application.services.user_service import UserService
from app.core.config import config
from app.domain.user.entities import User
from app.infrastructure.db import (
    ResumeImportUnitOfWork,
    UserUnitOfWork,
    VacancyUnitOfWork,
    async_session_factory,
)
from app.infrastructure.notifications import TelegramDocumentSender
from app.telegram.miniapp.auth import MiniAppUserContext, validate_init_data


def get_user_service() -> UserService:
    return UserService(UserUnitOfWork(async_session_factory))


def get_onboarding_service() -> OnboardingService:
    return OnboardingService(UserUnitOfWork(async_session_factory))


def get_resume_import_service() -> ResumeImportService:
    return ResumeImportService(ResumeImportUnitOfWork(async_session_factory))


def get_search_profile_service() -> SearchProfileService:
    return SearchProfileService()


def get_stats_service() -> StatsService:
    return StatsService(VacancyUnitOfWork(async_session_factory))


def get_export_service() -> ExportService:
    return ExportService(VacancyUnitOfWork(async_session_factory))


def get_document_sender() -> TelegramDocumentSender:
    return TelegramDocumentSender()


def parse_user_context(init_data: str) -> MiniAppUserContext:
    try:
        return validate_init_data(init_data, config.BOT_TOKEN)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def get_user_context(request: Request) -> MiniAppUserContext:
    """Только подписанный идентификатор, без выборки пользователя.

    Статус разбора фронт опрашивает каждые пару секунд, и полноценная
    загрузка профиля на каждый опрос — лишний запрос в базу.
    """
    return parse_user_context(request.headers.get("X-Telegram-Init-Data", ""))


async def get_current_user(
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    user_context = parse_user_context(init_data)
    user = await service.get_user_by_tg_id(user_context.tg_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    return user
