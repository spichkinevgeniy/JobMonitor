"""Одновременная отправка нескольких резюме одним пользователем.

FSM-защиты тут мало: StateFilter вычисляется диспетчером до входа в хендлер,
а Telegram отдаёт getUpdates пачкой. Замер на этом же стенде до фикса давал
5 одновременных обработок из 5 отправленных — при потолке ~120 МБ на разбор
это 600 МБ при 744 МБ свободных на проде.
"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime, timedelta

import pytest
from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Document, Message, Update, User

from app.application.services.resume_quota_service import QuotaDecision, QuotaRejection
from app.telegram.bot.routers import resume as resume_router

BOT_TOKEN = "123456:AAaaAAaaAAaaAAaaAAaaAAaaAAaaAAaaAAa"
TG_ID = 777


def _make_update(update_id: int, tg_id: int = TG_ID) -> Update:
    user = User(id=tg_id, is_bot=False, first_name="test")
    chat = Chat(id=tg_id, type="private")
    message = Message(
        message_id=update_id,
        date=datetime.now(),
        chat=chat,
        from_user=user,
        document=Document(
            file_id=f"file-{update_id}",
            file_unique_id=f"uniq-{update_id}",
            file_name="cv.pdf",
            file_size=1024,
        ),
    )
    return Update(update_id=update_id, message=message)


class _AlwaysAllowQuota:
    def __init__(self, uow: object) -> None:
        pass

    async def check(self, tg_id: int) -> QuotaDecision:
        return QuotaDecision(allowed=True)

    async def register(self, tg_id: int) -> None:
        pass


@pytest.fixture
def accepted(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Считаем, сколько загрузок дошло до разбора, и держим их в работе."""
    reached: list[str] = []

    def fake_parser(file_name: str) -> object:
        reached.append(file_name)
        raise RuntimeError("останавливаем обработку сразу после захвата")

    async def fake_answer(self: Message, *args: object, **kwargs: object) -> None:
        await asyncio.sleep(0.2)

    monkeypatch.setattr(resume_router.ParserFactory, "get_parser_by_extension", fake_parser)
    monkeypatch.setattr(Message, "answer", fake_answer)
    # Квота живёт в БД, а тут проверяется только захват — пропускаем всех.
    monkeypatch.setattr(resume_router, "ResumeQuotaService", _AlwaysAllowQuota)
    resume_router._active_resume_uploads.clear()
    return reached


@pytest.fixture(scope="module")
async def feed() -> AsyncIterator[Callable[[list[Update]], Awaitable[None]]]:
    """Роутер модульный: к диспетчеру он цепляется ровно один раз, отсюда и scope."""
    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(resume_router.router)

    async def _feed(updates: list[Update]) -> None:
        await asyncio.gather(*(dispatcher.feed_update(bot=bot, update=item) for item in updates))

    try:
        yield _feed
    finally:
        await bot.session.close()


class TestConcurrentUploads:
    async def test_burst_from_one_user_admits_only_one(
        self, accepted: list[str], feed: Callable[[list[Update]], Awaitable[None]]
    ) -> None:
        await feed([_make_update(i) for i in range(1, 6)])

        assert len(accepted) == 1

    async def test_guard_is_released_after_processing(
        self, accepted: list[str], feed: Callable[[list[Update]], Awaitable[None]]
    ) -> None:
        await feed([_make_update(1)])
        await feed([_make_update(2)])

        assert len(accepted) == 2
        assert resume_router._active_resume_uploads == set()

    async def test_different_users_are_not_blocked(
        self, accepted: list[str], feed: Callable[[list[Update]], Awaitable[None]]
    ) -> None:
        await feed([_make_update(1, tg_id=111), _make_update(2, tg_id=222)])

        assert len(accepted) == 2


class TestQuotaBlocksProcessing:
    @pytest.fixture
    def rejecting_quota(self, monkeypatch: pytest.MonkeyPatch) -> list[int]:
        registered: list[int] = []

        class _Rejecting:
            def __init__(self, uow: object) -> None:
                pass

            async def check(self, tg_id: int) -> QuotaDecision:
                return QuotaDecision(
                    allowed=False,
                    rejection=QuotaRejection.DAILY_QUOTA,
                    retry_after=timedelta(days=1),
                )

            async def register(self, tg_id: int) -> None:
                registered.append(tg_id)

        monkeypatch.setattr(resume_router, "ResumeQuotaService", _Rejecting)
        return registered

    async def test_rejected_upload_never_reaches_parser(
        self,
        accepted: list[str],
        rejecting_quota: list[int],
        feed: Callable[[list[Update]], Awaitable[None]],
    ) -> None:
        await feed([_make_update(1)])

        assert accepted == []

    async def test_rejected_upload_is_not_counted(
        self,
        accepted: list[str],
        rejecting_quota: list[int],
        feed: Callable[[list[Update]], Awaitable[None]],
    ) -> None:
        """Отказ не должен съедать квоту — иначе она не восстановится."""
        await feed([_make_update(1)])

        assert rejecting_quota == []

    async def test_guard_is_released_after_rejection(
        self,
        accepted: list[str],
        rejecting_quota: list[int],
        feed: Callable[[list[Update]], Awaitable[None]],
    ) -> None:
        await feed([_make_update(1)])

        assert resume_router._active_resume_uploads == set()
