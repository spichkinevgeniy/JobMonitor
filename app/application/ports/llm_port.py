from typing import Protocol

from app.application.dto.vacancy_dto import OutVacancyParse


class LLMUnavailableError(Exception):
    """Модель временно недоступна, и повторы не помогли.

    Сообщение в этом случае пропускается без счёта как сбой разбора: текст
    не виноват, дело в провайдере.
    """


class IVacancyLLMExtractor(Protocol):
    async def parse_vacancy(self, text: str) -> OutVacancyParse: ...
