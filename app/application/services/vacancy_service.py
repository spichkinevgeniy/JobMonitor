from uuid import uuid4

from app.application.dto import InfoRawVacancy, OutVacancyParse
from app.application.ports.llm_port import IVacancyLLMExtractor
from app.application.ports.observability_port import IObservabilityService
from app.application.ports.unit_of_work import VacancyUnitOfWork
from app.core.logger import get_app_logger
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.value_objects import VacancyId

logger = get_app_logger(__name__)


class VacancyService:
    def __init__(
        self,
        uow: VacancyUnitOfWork,
        extractor: IVacancyLLMExtractor,
        observability: IObservabilityService,
    ) -> None:
        self._uow = uow
        self._extractor = extractor
        self._observability = observability

    async def parse_message(self, raw_vacancy_info: InfoRawVacancy) -> OutVacancyParse | None:
        text = raw_vacancy_info.text.strip()
        if not text:
            return None

        logger.debug(
            f"LLM request (text_len={len(text)}, chat_id={raw_vacancy_info.chat_id}, "
            f"message_id={raw_vacancy_info.message_id})"
        )
        result = await self._extractor.parse_vacancy(text)
        if not result.is_vacancy:
            logger.info("Message is not a vacancy")
            return None

        logger.info(
            f"LLM parsed vacancy (specializations={[s.value for s in result.specializations]}, "
            f"languages={[language.value for language in result.primary_languages]}, "
            f"tech_stack={result.tech_stack}, min_exp_months={result.min_experience_months})"
        )
        return result

    async def save_vacancy(
        self,
        raw_vacancy_info: InfoRawVacancy,
        parse_result: OutVacancyParse,
    ) -> VacancyId:
        text = raw_vacancy_info.text.strip()
        if not text:
            raise ValueError("Vacancy text is empty")
        if raw_vacancy_info.mirror_chat_id is None or raw_vacancy_info.mirror_message_id is None:
            raise ValueError("Mirror chat/message ids are required")

        vacancy = Vacancy.create(
            vacancy_id=uuid4(),
            text=text,
            specializations_raw=[
                s.value for s in parse_result.specializations],
            languages_raw=[
                language.value for language in parse_result.primary_languages],
            tech_stack_raw=parse_result.tech_stack,
            min_experience_months=parse_result.min_experience_months,
            mirror_chat_id=raw_vacancy_info.mirror_chat_id,
            mirror_message_id=raw_vacancy_info.mirror_message_id,
            work_format=parse_result.work_format,
            salary_amount=parse_result.salary.amount if parse_result.salary else None,
            salary_currency=(
                parse_result.salary.currency.value
                if parse_result.salary and parse_result.salary.currency
                else None
            ),
        )
        async with self._uow:
            await self._uow.vacancies.upsert(vacancy)
        self._observability.observe_vacancy_collected(1)

        return vacancy.id
