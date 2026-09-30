"""Кнопки под вакансией в настоящей базе: объяснение, отметка и её отмена."""

from uuid import uuid4

from sqlalchemy import select

from app.application.services.vacancy_feedback_service import (
    VacancyFeedbackService,
    VacancySource,
)
from app.domain.matching.entities import MatchRejectionReason
from app.domain.shared import WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode
from app.domain.vacancy.entities import Vacancy
from app.infrastructure.db import (
    MatchingUnitOfWork,
    UserUnitOfWork,
    VacancyUnitOfWork,
    async_session_factory,
)
from app.infrastructure.db.models import VacancyDispatchLog

USER_ID = 42


def service() -> VacancyFeedbackService:
    return VacancyFeedbackService(lambda: MatchingUnitOfWork(async_session_factory))


async def sent_vacancy() -> Vacancy:
    """Пост из форума без формата работы — ушёл человеку со строгим фильтром формата."""
    vacancy = Vacancy.create(
        vacancy_id=uuid4(),
        text="Frontend-разработчик на React, формат обсуждается",
        specializations_raw=["Frontend"],
        skills_raw=["React", "TypeScript"],
        mirror_chat_id=-100,
        mirror_message_id=7,
        work_format=WorkFormat.UNDEFINED,
        source_channel="@front_end_jobs",
        source_message_id=16740,
        source_topic_id=2,
    )
    vacancies = VacancyUnitOfWork(async_session_factory)
    async with vacancies:
        await vacancies.vacancies.add(vacancy)

    users = UserUnitOfWork(async_session_factory)
    async with users:
        await users.users.add(
            User.create(
                tg_id=USER_ID,
                cv_specializations_raw=["Frontend"],
                cv_skills_raw=["React"],
                cv_work_format=WorkFormat.REMOTE,
                filter_work_format_mode=FilterMode.STRICT,
            )
        )

    async with async_session_factory() as session:
        session.add(
            VacancyDispatchLog(
                user_tg_id=USER_ID,
                vacancy_id=vacancy.id.value,
                matched_skills=["React"],
                matched_specializations=["Frontend"],
            )
        )
        await session.commit()
    return vacancy


async def stored_feedback(vacancy: Vacancy) -> tuple[str | None, bool]:
    async with async_session_factory() as session:
        feedback, at = (
            await session.execute(
                select(VacancyDispatchLog.feedback, VacancyDispatchLog.feedback_at).where(
                    VacancyDispatchLog.vacancy_id == vacancy.id.value
                )
            )
        ).one()
    return feedback, at is not None


async def test_explanation_comes_from_the_dispatch_snapshot() -> None:
    vacancy = await sent_vacancy()

    explanation = await service().explain(vacancy.id.value, USER_ID)

    assert explanation is not None
    assert explanation.matched_specializations == ["Frontend"]
    assert explanation.matched_skills == ["React"]
    assert explanation.unchecked_filters == [MatchRejectionReason.FORMAT]
    assert explanation.user_work_format == "REMOTE"


async def test_nothing_to_explain_to_someone_else() -> None:
    vacancy = await sent_vacancy()

    assert await service().explain(vacancy.id.value, USER_ID + 1) is None


async def test_rejection_is_stored_and_undone() -> None:
    vacancy = await sent_vacancy()
    feedback = service()

    await feedback.reject(vacancy.id.value, USER_ID)
    assert await stored_feedback(vacancy) == ("rejected", True)

    await feedback.undo_rejection(vacancy.id.value, USER_ID)
    assert await stored_feedback(vacancy) == (None, False)


async def test_forum_source_keeps_its_topic() -> None:
    vacancy = await sent_vacancy()

    source = await service().source_of(vacancy.id.value)

    assert source == VacancySource(
        channel="@front_end_jobs",
        url="https://t.me/front_end_jobs/2/16740",
    )
