"""Одновременная отправка нескольких резюме одним пользователем."""

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
ALLOW = QuotaDecision(allowed=True)
DENY = QuotaDecision(
    allowed=False,
    rejection=QuotaRejection.DAILY_QUOTA,
    retry_after=timedelta(days=1),
)


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


class _Quota:
    """Квота живёт в БД, тут проверяется только захват."""

    def __init__(self, decision: QuotaDecision) -> None:
        self._decision = decision
        self.registered: list[int] = []

    async def check(self, tg_id: int) -> QuotaDecision:
        return self._decision

    async def register(self, tg_id: int) -> None:
        self.registered.append(tg_id)


Feed = Callable[[list[Update], _Quota], Awaitable[None]]


@pytest.fixture
def accepted(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Считает загрузки, дошедшие до разбора, и держит их в работе."""
    reached: list[str] = []

    def fake_parser(file_name: str) -> object:
        reached.append(file_name)
        raise RuntimeError("останавливаем обработку сразу после захвата")

    async def fake_answer(self: Message, *args: object, **kwargs: object) -> None:
        await asyncio.sleep(0.2)

    monkeypatch.setattr(resume_router.ParserFactory, "get_parser_by_extension", fake_parser)
    monkeypatch.setattr(Message, "answer", fake_answer)
    resume_router._active_resume_uploads.clear()
    return reached


@pytest.fixture(scope="module")
async def feed() -> AsyncIterator[Feed]:
    """Роутер модульный: к диспетчеру он цепляется один раз, отсюда и scope."""
    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(resume_router.router)

    async def _feed(updates: list[Update], quota: _Quota) -> None:
        # Сервисы в проде кладёт ServicesMiddleware; до сохранения профиля
        # загрузка тут не доходит, поэтому сервис пользователей — заглушка.
        await asyncio.gather(
            *(
                dispatcher.feed_update(
                    bot=bot, update=item, resume_quota=quota, user_service=object()
                )
                for item in updates
            )
        )

    try:
        yield _feed
    finally:
        await bot.session.close()


class TestConcurrentUploads:
    async def test_burst_from_one_user_admits_only_one(
        self, accepted: list[str], feed: Feed
    ) -> None:
        await feed([_make_update(i) for i in range(1, 6)], _Quota(ALLOW))

        assert len(accepted) == 1

    async def test_guard_is_released_after_processing(
        self, accepted: list[str], feed: Feed
    ) -> None:
        await feed([_make_update(1)], _Quota(ALLOW))
        await feed([_make_update(2)], _Quota(ALLOW))

        assert len(accepted) == 2
        assert resume_router._active_resume_uploads == set()

    async def test_different_users_are_not_blocked(self, accepted: list[str], feed: Feed) -> None:
        await feed([_make_update(1, tg_id=111), _make_update(2, tg_id=222)], _Quota(ALLOW))

        assert len(accepted) == 2


class TestQuotaBlocksProcessing:
    async def test_rejected_upload_never_reaches_parser(
        self, accepted: list[str], feed: Feed
    ) -> None:
        await feed([_make_update(1)], _Quota(DENY))

        assert accepted == []

    async def test_rejected_upload_is_not_counted(self, accepted: list[str], feed: Feed) -> None:
        quota = _Quota(DENY)

        await feed([_make_update(1)], quota)

        assert quota.registered == []

    async def test_guard_is_released_after_rejection(self, accepted: list[str], feed: Feed) -> None:
        await feed([_make_update(1)], _Quota(DENY))

        assert resume_router._active_resume_uploads == set()
