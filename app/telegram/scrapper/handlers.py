import logfire
from telethon import TelegramClient, events  # type: ignore[import-untyped]
from telethon.errors import (  # type: ignore[import-untyped]
    ChatForwardsRestrictedError,
    MessageIdInvalidError,
)
from telethon.tl.custom.message import Message  # type: ignore[import-untyped]

from app.application.dto import InfoRawVacancy
from app.application.ports.observability_port import IObservabilityService, SkipReason
from app.application.services.channel_message_service import ChannelMessageService
from app.core.config import config
from app.core.logger import get_app_logger
from app.telegram.scrapper.channels import normalized_channels

logger = get_app_logger(__name__)
scraper_logfire = logfire.with_tags("scraper")

MIN_VACANCY_TEXT_LENGTH = 120


class TelegramScraper:
    """Слушает каналы и пересылает подходящие сообщения в зеркало.

    Что делать с сообщением дальше, решает ChannelMessageService.
    """

    def __init__(
        self,
        client: TelegramClient,
        messages: ChannelMessageService,
        observability: IObservabilityService,
    ) -> None:
        self.client = client
        self._messages = messages
        self._observability = observability

    async def _message_handler(self, event: events.NewMessage.Event) -> None:
        message = event.message
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
                if message_info is not None:
                    await self._messages.process(message_info)
        except Exception:
            # Ожидаемые исходы сервис гасит сам, сюда доходят только сбои.
            # Ловим всё: упавший обработчик не должен остановить скрапер.
            self._observability.observe_message_skipped(SkipReason.PARSE_FAILED)
            logger.exception(
                "Scraper message handling failed (chat_id=%s, message_id=%s)",
                event.chat_id,
                message.id,
            )

    async def start(self) -> None:
        channels = await self._resolve_valid_channels(normalized_channels(config.CHANNELS))
        logger.info("Scraper listens channels: %s", channels)
        if not channels:
            logger.warning("Scraper start skipped: no valid Telegram channels were resolved.")
            return
        self.client.add_event_handler(
            self._message_handler,
            events.NewMessage(chats=channels),
        )
        logger.info("Scraper started.")
        await self.client.run_until_disconnected()

    async def _resolve_valid_channels(self, channels: list[str | int]) -> list[str | int]:
        valid_channels: list[str | int] = []

        for channel in channels:
            try:
                await self.client.get_input_entity(channel)
            except Exception:
                logger.warning(
                    "Scraper channel skipped: failed to resolve Telegram entity %r",
                    channel,
                    exc_info=True,
                )
                continue
            valid_channels.append(channel)

        return valid_channels

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
    def _source_topic_id(message: Message) -> int | None:
        """Тема форума, в которой опубликовано сообщение.

        Без неё ссылка вида t.me/группа/сообщение в форуме не открывается.
        reply_to_top_id указывает на корень темы, reply_to_msg_id — на само
        сообщение темы, когда ответ идёт прямо в её начало.
        """
        reply_to = getattr(message, "reply_to", None)
        if reply_to is None or not getattr(reply_to, "forum_topic", False):
            return None
        top_id = getattr(reply_to, "reply_to_top_id", None)
        return top_id or getattr(reply_to, "reply_to_msg_id", None)

    @staticmethod
    def _source_username(event: events.NewMessage.Event) -> str | None:
        """Только @username: по нему собирается ссылка на исходный пост."""
        username = getattr(event.chat, "username", None)
        return f"@{username}" if username else None

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
            self._observability.observe_message_skipped(SkipReason.TOO_SHORT)
            scraper_logfire.info(
                "Message skipped: empty text",
                chat_id=event.chat_id,
                message_id=message.id,
            )
            return None

        if len(" ".join(text.split())) < MIN_VACANCY_TEXT_LENGTH:
            self._observability.observe_message_skipped(SkipReason.TOO_SHORT)
            scraper_logfire.info(
                "Message skipped: too short",
                chat_id=event.chat_id,
                message_id=message.id,
                text_length=len(text),
            )
            return None

        try:
            mirror_msg: Message = await self.client.forward_messages(
                config.MIRROR_CHANNEL,
                message,
            )
        except (MessageIdInvalidError, ChatForwardsRestrictedError) as exc:
            # Не сбой, а отказ: пост удалили раньше, чем мы его переслали, или
            # канал запретил пересылку. Считаются отдельно — так видно, если
            # отказы вдруг скопятся в одном канале.
            reason = (
                SkipReason.FORWARDS_RESTRICTED
                if isinstance(exc, ChatForwardsRestrictedError)
                else SkipReason.SOURCE_UNAVAILABLE
            )
            self._observability.observe_message_skipped(reason)
            logger.warning(
                "Message not mirrored: %s (source_chat_id=%s, source_channel=%s, "
                "source_message_id=%s)",
                reason.value,
                event.chat_id,
                self._source_channel_name(event),
                message.id,
            )
            return None
        except Exception:
            source_channel = self._source_channel_name(event)
            preview = self._message_preview(text)
            self._observability.observe_message_skipped(SkipReason.MIRROR_FAILED)
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
            source_channel=self._source_username(event),
            source_topic_id=self._source_topic_id(message),
        )
