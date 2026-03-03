from app.application.dto import OutVacancyParse
from app.application.ports.llm_port import IVacancyLLMExtractor
from app.infrastructure.llm import get_vacancy_parse_agent


class GoogleVacancyLLMExtractor(IVacancyLLMExtractor):
    def __init__(self) -> None:
        self._agent = get_vacancy_parse_agent()

    async def parse_vacancy(self, text: str) -> OutVacancyParse:
        result = await self._agent.run(
            user_prompt=f"Текст вакансии:\n{text}",
            metadata={"pipeline": "vacancy_ingest"},
        )
        return result.output
