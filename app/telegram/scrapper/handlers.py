import logfire
from aiogram import Bot
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from telethon import TelegramClient, events  # type: ignore[import-untyped]
from telethon.tl.custom.message import Message  # type: ignore[import-untyped]

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
from app.infrastructure.llm_runtime import TemporaryLLMUnavailableError
from app.infrastructure.notifications import TelegramNotificationService
from app.telegram.scrapper.channels import normalized_channels

logger = get_app_logger(__name__)
scraper_logfire = logfire.with_tags("scraper")


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
        message = event.message
        content_hash: str | None = None
        vacancy_id: str | None = None

        try:
            with scraper_logfire.span(
                "scraper.handle_message",
                chat_id=event.chat_id,
                message_id=message.id,
            ):
                scraper_logfire.info(
                    "Message received",
                    chat_id=event.chat_id,
                    message_id=message.id,
                )
                message_info = await self._send_to_mirror(event)
                if not message_info:
                    return

                content_hash = Vacancy.compute_content_hash(message_info.text).value
                check_uow = VacancyUnitOfWork(self._session_factory)
                async with check_uow:
                    exists = await check_uow.vacancies.exists_by_content_hash(
                        ContentHash(content_hash)
                    )
                if exists:
                    scraper_logfire.info(
                        "Duplicate vacancy skipped",
                        chat_id=event.chat_id,
                        message_id=message.id,
                        content_hash=content_hash,
                        source="prefilter",
                    )
                    return

                uow = VacancyUnitOfWork(self._session_factory)
                v_service = VacancyService(uow, self._extractor, self._observability)
                parse_result = await v_service.parse_message(message_info)
                if not parse_result:
                    return

                saved_vacancy_id = await v_service.save_vacancy(message_info, parse_result)
                vacancy_id = str(saved_vacancy_id.value)
                scraper_logfire.info(
                    "Vacancy saved",
                    chat_id=event.chat_id,
                    message_id=message.id,
                    content_hash=content_hash,
                    vacancy_id=vacancy_id,
                )

                matcher = MatcherService(
                    MatchingUnitOfWork(self._session_factory),
                    self._notification_service,
                    self._observability,
                )
                await matcher.match_vacancy(saved_vacancy_id)
        except IntegrityError:
            scraper_logfire.info(
                "Duplicate vacancy skipped",
                chat_id=event.chat_id,
                message_id=message.id,
                content_hash=content_hash,
                source="save",
            )
        except TemporaryLLMUnavailableError:
            scraper_logfire.warning(
                "Message skipped: llm temporarily unavailable",
                chat_id=event.chat_id,
                message_id=message.id,
                content_hash=content_hash,
                vacancy_id=vacancy_id,
            )
        except Exception:
            logger.exception(
                "Scraper message handling failed (chat_id=%s, message_id=%s, content_hash=%s, "
                "vacancy_id=%s)",
                event.chat_id,
                message.id,
                content_hash,
                vacancy_id,
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
            scraper_logfire.info(
                "Message skipped: empty text",
                chat_id=event.chat_id,
                message_id=message.id,
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

        return InfoRawVacancy(
            mirror_chat_id=mirror_msg.chat_id,
            mirror_message_id=mirror_msg.id,
            text=text,
            chat_id=event.chat_id,
            message_id=message.id,
        )
