from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.application.services.export_service import ExportService
from app.application.services.stats_service import StatsService
from app.application.services.user_service import UserService
from app.core.config import config
from app.domain.user.entities import User
from app.infrastructure.db import UserUnitOfWork, VacancyUnitOfWork, async_session_factory
from app.infrastructure.notifications import TelegramDocumentSender
from app.telegram.miniapp.auth import MiniAppUserContext, validate_init_data


def get_user_service() -> UserService:
    return UserService(UserUnitOfWork(async_session_factory))


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
