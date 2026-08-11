from uuid import UUID

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.notification_port import DispatchTarget, INotificationService
from app.core.logger import get_app_logger
from app.core.privacy import user_ref
from app.domain.user.value_objects import UserId
from app.infrastructure.db.models import VacancyDispatchLog
from app.infrastructure.db.uow.base import SQLAlchemyUnitOfWork
from app.infrastructure.db.uow.user_uow import UserUnitOfWork
from app.telegram.bot.keyboards import get_vacancy_kb

logger = get_app_logger(__name__)


class TelegramNotificationService(INotificationService):
    def __init__(self, bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._bot = bot
        self._session_factory = session_factory

    async def dispatch_vacancy(
        self,
        vacancy_id: UUID,
        mirror_chat_id: int,
        mirror_message_id: int,
        targets: list[DispatchTarget],
        source_channel: str | None = None,
        source_url: str | None = None,
    ) -> None:
        logger.info(
            "Dispatch vacancy %s (%s:%s) to %s users",
            vacancy_id,
            mirror_chat_id,
            mirror_message_id,
            len(targets),
        )
        for target in targets:
            user_id = target.user_id
            try:
                # copy_message вместо forward_message: к пересылке Telegram не
                # даёт прицепить кнопки. Шапка «Переслано из» пропадает, но она
                # показывала приватный зеркальный канал и пользователю бесполезна.
                await self._bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=mirror_chat_id,
                    message_id=mirror_message_id,
                    reply_markup=get_vacancy_kb(
                        str(vacancy_id),
                        source_channel=source_channel,
                        source_url=source_url,
                    ),
                )
                await self._log_dispatch(user_id, vacancy_id, target)
            except TelegramForbiddenError:
                logger.warning(
                    "Failed to send vacancy %s to user %s: bot forbidden",
                    vacancy_id,
                    user_ref(user_id),
                )
                await self._deactivate_user(user_id)
            except Exception:
                logger.exception(
                    "Failed to send vacancy %s to user %s",
                    vacancy_id,
                    user_ref(user_id),
                )

        logger.info("Dispatch finished for vacancy %s", vacancy_id)

    async def _log_dispatch(self, user_id: int, vacancy_id: UUID, target: DispatchTarget) -> None:
        try:
            async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
                assert uow.session is not None
                uow.session.add(
                    VacancyDispatchLog(
                        user_tg_id=user_id,
                        vacancy_id=vacancy_id,
                        matched_skills=target.matched_skills,
                        matched_specializations=target.matched_specializations,
                    )
                )
        except Exception:
            logger.exception(
                "Failed to log dispatch of vacancy %s to user %s", vacancy_id, user_ref(user_id)
            )

    async def _deactivate_user(self, user_id: int) -> None:
        try:
            async with UserUnitOfWork(self._session_factory) as uow:
                user = await uow.users.get_by_tg_id_for_update(UserId(user_id))
                if user is not None and user.is_active:
                    user.is_active = False
                    await uow.users.update(user)
        except Exception:
            logger.exception(
                "Failed to deactivate user %s after bot-forbidden error", user_ref(user_id)
            )
