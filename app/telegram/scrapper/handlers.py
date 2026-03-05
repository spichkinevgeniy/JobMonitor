from aiogram import Bot
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message

from app.application.dto import InfoRawVacancy
from app.application.ports.llm_port import IVacancyLLMExtractor
from app.application.ports.observability_port import IObservabilityService
from app.application.services.matcher_service import MatcherService
from app.application.services.vacancy_service import VacancyService
from app.core.config import config
from app.core.logger import get_app_logger
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.value_objects import ContentHash
from app.infrastructure.db import MatchingUnitOfWork, VacancyUnitOfWork
from app.infrastructure.notifications import TelegramNotificationService
from app.telegram.scrapper.channels import normalized_channels

logger = get_app_logger(__name__)


class TelegramScraper:
    def __init__(
        self,
        client: TelegramClient,
        bot: Bot,
        session_factory: async_sessionmaker[AsyncSession],
        extractor: IVacancyLLMExtractor,
        observability: IObservabilityService,
    ) -> None:
        self.client = client
        self._session_factory = session_factory
        self._extractor = extractor
        self._observability = observability
        self._notification_service = TelegramNotificationService(bot)

    async def _message_handler(self, event: events.NewMessage.Event) -> None:
        try:
            logger.info(
                f"Received message (chat_id={event.chat_id}, message_id={event.message.id})"
            )
            message_info = await self._send_to_mirror(event)
            if not message_info:
                return

            content_hash = Vacancy.compute_content_hash(message_info.text).value
            check_uow = VacancyUnitOfWork(self._session_factory)
            async with check_uow:
                exists = await check_uow.vacancies.exists_by_content_hash(ContentHash(content_hash))
            if exists:
                logger.info(
                    f"Duplicate vacancy skipped before parse (content_hash={content_hash}, "
                    f"chat_id={event.chat_id}, message_id={event.message.id})"
                )
                return

            uow = VacancyUnitOfWork(self._session_factory)
            v_service = VacancyService(uow, self._extractor, self._observability)
            parse_result = await v_service.parse_message(message_info)
            if not parse_result:
                return
            try:
                vacancy_id = await v_service.save_vacancy(message_info, parse_result)
                logger.info(
                    f"Vacancy saved (content_hash={content_hash}, "
                    f"chat_id={event.chat_id}, message_id={event.message.id})"
                )
                try:
                    matcher = MatcherService(
                        MatchingUnitOfWork(self._session_factory),
                        self._notification_service,
                        self._observability,
                    )
                    matched_user_ids = await matcher.match_vacancy(vacancy_id)
                    logger.info(
                        "Matching completed for vacancy %s: %s users ready for dispatch",
                        vacancy_id.value,
                        len(matched_user_ids),
                    )
                except Exception:
                    logger.exception(
                        "Matching failed (vacancy_id=%s, chat_id=%s, message_id=%s)",
                        vacancy_id.value,
                        event.chat_id,
                        event.message.id,
                    )
            except IntegrityError:
                logger.info(
                    f"Duplicate vacancy skipped (content_hash={content_hash}, "
                    f"chat_id={event.chat_id}, message_id={event.message.id})"
                )
        except Exception:
            logger.exception(
                f"Handler failed (chat_id={event.chat_id}, message_id={event.message.id})"
            )

    async def start(self) -> None:
        channels = normalized_channels(config.CHANNELS)
        logger.info("Scraper listens channels: %s", channels)
        self.client.add_event_handler(
            self._message_handler,
            events.NewMessage(chats=channels),
        )
        logger.info("Scraper started.")
        await self.client.run_until_disconnected()

    @staticmethod
    def _source_channel_name(event: events.NewMessage.Event) -> str:
        chat = event.chat
        username = getattr(chat, "username", None)
        title = getattr(chat, "title", None)
        if username:
            return f"@{username}"
        if title:
            return str(title)
        return "unknown"

    @staticmethod
    def _message_preview(text: str, limit: int = 300) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= limit:
            return normalized
        return f"{normalized[:limit]}..."

    async def _send_to_mirror(self, event: events.NewMessage.Event) -> InfoRawVacancy | None:
        message: Message = event.message
        text = message.text or ""

        if not text:
            logger.info(
                f"Skipping message with empty text (chat_id={event.chat_id}, "
                f"message_id={message.id})"
            )
            return None

        try:
            mirror_msg: Message = await self.client.forward_messages(
                config.MIRROR_CHANNEL,
                message,
            )
        except Exception:
            source_channel = self._source_channel_name(event)
            preview = self._message_preview(text)
            logger.exception(
                "Failed to forward message to mirror (source_chat_id=%s, source_channel=%s, "
                "source_message_id=%s, source_message_preview=%r)",
                event.chat_id,
                source_channel,
                message.id,
                preview,
            )
            return None

        logger.info(
            f"Message forwarded to mirror (source_chat_id={event.chat_id}, "
            f"source_message_id={message.id}, mirror_chat_id={mirror_msg.chat_id}, "
            f"mirror_message_id={mirror_msg.id})"
        )

        return InfoRawVacancy(
            mirror_chat_id=mirror_msg.chat_id,
            mirror_message_id=mirror_msg.id,
            text=text,
            chat_id=event.chat_id,
            message_id=message.id,
        )
