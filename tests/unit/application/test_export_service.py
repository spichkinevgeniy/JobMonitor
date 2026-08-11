"""Выгрузка вакансий: границы выборки."""

from types import TracebackType
from uuid import uuid4

from app.application.services.export_service import (
    MAX_EXPORT_VACANCIES,
    ExportFormat,
    ExportService,
    _fence_for,
)
from app.domain.shared.value_objects import WorkFormat
from app.domain.vacancy.entities import DispatchedVacancy, Vacancy

TG_ID = 777


class FakeVacancyRepository:
    def __init__(self, dispatched: list[DispatchedVacancy]) -> None:
        self._dispatched = dispatched
        self.calls: list[int | None] = []

    async def find_dispatched_for_user(
        self, user_tg_id: int, limit: int | None = None
    ) -> list[DispatchedVacancy]:
        self.calls.append(limit)
        return self._dispatched[:limit] if limit is not None else self._dispatched


class FakeUnitOfWork:
    def __init__(self, dispatched: list[DispatchedVacancy] | None = None) -> None:
        self.vacancies = FakeVacancyRepository(dispatched or [])

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


async def test_build_limits_the_query() -> None:
    uow = FakeUnitOfWork()
    service = ExportService(uow)  # type: ignore[arg-type]

    await service.build(TG_ID, ExportFormat.JSON)

    assert uow.vacancies.calls == [MAX_EXPORT_VACANCIES]


async def test_build_returns_none_without_history() -> None:
    uow = FakeUnitOfWork()
    service = ExportService(uow)  # type: ignore[arg-type]

    assert await service.build(TG_ID, ExportFormat.JSON) is None


class TestMarkdownFence:
    def test_plain_text_uses_three_backticks(self) -> None:
        assert _fence_for("обычный текст вакансии") == "```"

    def test_fence_outgrows_backticks_inside_text(self) -> None:
        assert _fence_for("код: ```python\nprint(1)\n```") == "````"

    def test_fence_outgrows_the_longest_run(self) -> None:
        assert _fence_for("`a`` b ````` c ``") == "``````"

    def test_injected_text_stays_inside_the_block(self) -> None:
        """Иначе постом в чужом канале можно вылезти из блока в разметку."""
        text = "```\n# чужой заголовок\n[ссылка](http://evil)"
        fence = _fence_for(text)

        assert fence not in text


class TestSourceLink:
    def _vacancy(self, channel: str | None, message_id: int | None) -> Vacancy:
        return Vacancy.create(
            vacancy_id=uuid4(),
            text="Вакансия",
            specializations_raw=["Backend"],
            skills_raw=["Python"],
            mirror_chat_id=1,
            mirror_message_id=2,
            work_format=WorkFormat.REMOTE,
            source_channel=channel,
            source_message_id=message_id,
        )

    def test_builds_link_to_the_original_post(self) -> None:
        vacancy = self._vacancy("@python_jobs", 4242)

        assert vacancy.source_url == "https://t.me/python_jobs/4242"

    def test_no_link_for_old_vacancies(self) -> None:
        """Собранные до появления колонок — источник восстановить неоткуда."""
        assert self._vacancy(None, None).source_url is None

    def test_no_link_without_message_id(self) -> None:
        assert self._vacancy("@python_jobs", None).source_url is None

    def test_no_link_for_private_channel(self) -> None:
        """Без @username публичной ссылки не существует."""
        assert self._vacancy("Закрытый канал", 4242).source_url is None
