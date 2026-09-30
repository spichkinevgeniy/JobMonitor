from collections.abc import Callable

import logfire

from app.application.dto import InfoRawVacancy
from app.application.ports.llm_port import IVacancyLLMExtractor, LLMUnavailableError
from app.application.ports.notification_port import INotificationService
from app.application.ports.observability_port import IObservabilityService, SkipReason
from app.application.ports.unit_of_work import MatchingUnitOfWork, VacancyUnitOfWork
from app.application.services.matcher_service import MatcherService
from app.application.services.vacancy_service import VacancyService
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.exceptions import DuplicateVacancyError
from app.domain.vacancy.value_objects import ContentHash

application_logfire = logfire.with_tags("application")


class ChannelMessageService:
    """Путь сообщения из канала: дубль → разбор → сохранение → подбор.

    Сюда сообщение приходит уже пересланным в зеркало: получение события и
    пересылка — дело Telegram-слоя. Здесь только решение, что с ним делать.
    Ожидаемые исходы — дубль, «не вакансия», недоступная модель — считаются
    и гасятся здесь. Всё остальное — сбой, и его ловит вызывающий.
    """

    def __init__(
        self,
        vacancy_uow: Callable[[], VacancyUnitOfWork],
        matching_uow: Callable[[], MatchingUnitOfWork],
        extractor: IVacancyLLMExtractor,
        notifications: INotificationService,
        observability: IObservabilityService,
    ) -> None:
        self._vacancy_uow = vacancy_uow
        self._matching_uow = matching_uow
        self._extractor = extractor
        self._notifications = notifications
        self._observability = observability

    async def process(self, message: InfoRawVacancy) -> None:
        content_hash = Vacancy.compute_content_hash(message.text)
        with application_logfire.span(
            "message.process",
            chat_id=message.chat_id,
            message_id=message.message_id,
            content_hash=content_hash.value,
        ):
            if await self._already_saved(content_hash):
                self._skip_duplicate(message, content_hash, source="prefilter")
                return

            vacancies = VacancyService(self._vacancy_uow(), self._extractor, self._observability)
            try:
                parsed = await vacancies.parse_message(message)
            except LLMUnavailableError:
                application_logfire.warning(
                    "Message skipped: llm temporarily unavailable",
                    chat_id=message.chat_id,
                    message_id=message.message_id,
                )
                return
            if parsed is None:
                return

            try:
                vacancy_id = await vacancies.save_vacancy(message, parsed)
            except DuplicateVacancyError:
                self._skip_duplicate(message, content_hash, source="save")
                return
            application_logfire.info(
                "Vacancy saved",
                chat_id=message.chat_id,
                message_id=message.message_id,
                vacancy_id=str(vacancy_id.value),
            )

            matcher = MatcherService(self._matching_uow(), self._notifications, self._observability)
            await matcher.match_vacancy(vacancy_id)

    async def _already_saved(self, content_hash: ContentHash) -> bool:
        uow = self._vacancy_uow()
        async with uow:
            return await uow.vacancies.exists_by_content_hash(content_hash)

    def _skip_duplicate(
        self, message: InfoRawVacancy, content_hash: ContentHash, *, source: str
    ) -> None:
        self._observability.observe_message_skipped(SkipReason.DUPLICATE)
        application_logfire.info(
            "Duplicate vacancy skipped",
            chat_id=message.chat_id,
            message_id=message.message_id,
            content_hash=content_hash.value,
            source=source,
        )
