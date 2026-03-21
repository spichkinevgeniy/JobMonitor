from app.application.dto import OutVacancyParse
from app.application.ports.llm_port import IVacancyLLMExtractor
from app.infrastructure.llm import get_vacancy_parse_agent
from app.infrastructure.llm_runtime import run_with_llm_retry


class GoogleVacancyLLMExtractor(IVacancyLLMExtractor):
    def __init__(self) -> None:
        self._agent = get_vacancy_parse_agent()

    async def parse_vacancy(self, text: str) -> OutVacancyParse:
        result = await run_with_llm_retry(
            "vacancy_parse",
            lambda: self._agent.run(
                user_prompt=(
                    f"Проанализируй текст и сначала определи, является ли он вакансией:\n{text}"
                ),
                metadata={"pipeline": "vacancy_ingest"},
            ),
        )
        return result.output
