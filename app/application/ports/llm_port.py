from typing import Protocol

from app.application.dto.vacancy_dto import OutVacancyParse


class IVacancyLLMExtractor(Protocol):
    async def parse_vacancy(self, text: str) -> OutVacancyParse: ...
