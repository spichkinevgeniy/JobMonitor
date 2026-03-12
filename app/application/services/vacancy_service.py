from uuid import uuid4

import logfire

from app.application.dto import InfoRawVacancy, OutVacancyParse
from app.application.ports.llm_port import IVacancyLLMExtractor
from app.application.ports.observability_port import IObservabilityService
from app.application.ports.unit_of_work import VacancyUnitOfWork
from app.core.logger import get_app_logger
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.value_objects import VacancyId

logger = get_app_logger(__name__)
application_logfire = logfire.with_tags("application")


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

        with application_logfire.span(
            "vacancy.parse_message",
            chat_id=raw_vacancy_info.chat_id,
            message_id=raw_vacancy_info.message_id,
            text_len=len(text),
        ):
            logger.debug(
                "LLM request (text_len=%s, chat_id=%s, message_id=%s)",
                len(text),
                raw_vacancy_info.chat_id,
                raw_vacancy_info.message_id,
            )
            result = await self._extractor.parse_vacancy(text)
            if not result.is_vacancy:
                application_logfire.info(
                    "Message is not a vacancy",
                    chat_id=raw_vacancy_info.chat_id,
                    message_id=raw_vacancy_info.message_id,
                    text_len=len(text),
                )
                self._observability.observe_not_vacancy_detected(1)
                return None

            application_logfire.info(
                "Vacancy parsed",
                chat_id=raw_vacancy_info.chat_id,
                message_id=raw_vacancy_info.message_id,
                specializations=[item.value for item in result.specializations],
                skills=[item.value for item in result.skills],
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

        with application_logfire.span(
            "vacancy.save",
            chat_id=raw_vacancy_info.chat_id,
            message_id=raw_vacancy_info.message_id,
            mirror_chat_id=raw_vacancy_info.mirror_chat_id,
            mirror_message_id=raw_vacancy_info.mirror_message_id,
        ):
            vacancy = Vacancy.create(
                vacancy_id=uuid4(),
                text=text,
                specializations_raw=[s.value for s in parse_result.specializations],
                skills_raw=[skill.value for skill in parse_result.skills],
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
