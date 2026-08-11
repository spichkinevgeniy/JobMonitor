from datetime import UTC, datetime
from uuid import UUID

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, update

from app.application.ports.observability_port import Feature
from app.core.logger import get_app_logger
from app.domain.user.value_objects import FilterMode, LevelFilterMode
from app.infrastructure.db import async_session_factory
from app.infrastructure.db.models import User as UserModel
from app.infrastructure.db.models import Vacancy as VacancyModel
from app.infrastructure.db.models import VacancyDispatchLog
from app.infrastructure.observability import observe_feature
from app.telegram.bot.keyboards import (
    VACANCY_REJECT_CALLBACK_PREFIX,
    VACANCY_UNDO_CALLBACK_PREFIX,
    VACANCY_WHY_CALLBACK_PREFIX,
    get_vacancy_kb,
)
from app.telegram.bot.views import (
    build_reason_caveat_experience,
    build_reason_caveat_format,
    build_reason_caveat_grade,
    build_reason_caveat_salary,
    build_vacancy_reason_text,
)

router = Router()
logger = get_app_logger(__name__)

FEEDBACK_REJECTED = "rejected"


def _vacancy_id(data: str, prefix: str) -> UUID | None:
    try:
        return UUID(data.removeprefix(prefix))
    except ValueError:
        return None


async def _source_of(vacancy_id: UUID) -> tuple[str | None, str | None]:
    """Кнопку источника надо вернуть на место при пересборке клавиатуры."""
    async with async_session_factory() as session:
        row = (
            await session.execute(
                select(VacancyModel.source_channel, VacancyModel.source_message_id).where(
                    VacancyModel.id == vacancy_id
                )
            )
        ).first()
    if row is None or not row.source_channel or row.source_message_id is None:
        return None, None
    if not row.source_channel.startswith("@"):
        return row.source_channel, None
    return row.source_channel, f"https://t.me/{row.source_channel[1:]}/{row.source_message_id}"


def _caveats(vacancy: VacancyModel, user: UserModel) -> list[str]:
    """Что объяснять: только поля, из-за отсутствия которых вакансия прошла
    вопреки настройке человека.

    Повторяет правила evaluate_match: там пустое поле означает «не отсеиваем»,
    и именно это выглядит для человека необъяснимым.
    """
    lines: list[str] = []
    if (
        vacancy.work_format == "UNDEFINED"
        and user.filter_work_format_mode == FilterMode.STRICT.value
        and user.cv_work_format
    ):
        lines.append(build_reason_caveat_format(user.cv_work_format))
    if (
        vacancy.grade == "UNDEFINED"
        and user.filter_grade_mode != LevelFilterMode.IGNORE.value
        and user.cv_grade
    ):
        lines.append(build_reason_caveat_grade())
    if (
        vacancy.experience_level == "UNDEFINED"
        and user.filter_experience_mode != LevelFilterMode.IGNORE.value
        and user.cv_experience_level
    ):
        lines.append(build_reason_caveat_experience())
    if (
        vacancy.salary_amount is None
        and user.filter_salary_mode == FilterMode.STRICT.value
        and user.cv_salary_amount
    ):
        lines.append(build_reason_caveat_salary())
    return lines


@router.callback_query(F.data.startswith(VACANCY_WHY_CALLBACK_PREFIX))
async def explain_vacancy(callback: CallbackQuery) -> None:
    vacancy_id = _vacancy_id(callback.data or "", VACANCY_WHY_CALLBACK_PREFIX)
    if vacancy_id is None or callback.from_user is None:
        await callback.answer()
        return

    async with async_session_factory() as session:
        row = (
            await session.execute(
                select(
                    VacancyDispatchLog.matched_skills,
                    VacancyDispatchLog.matched_specializations,
                    VacancyModel,
                    UserModel,
                )
                .join(VacancyModel, VacancyModel.id == VacancyDispatchLog.vacancy_id)
                .join(UserModel, UserModel.tg_id == VacancyDispatchLog.user_tg_id)
                .where(VacancyDispatchLog.vacancy_id == vacancy_id)
                .where(VacancyDispatchLog.user_tg_id == callback.from_user.id)
            )
        ).first()

    await callback.answer()
    if row is None or not isinstance(callback.message, Message):
        return

    observe_feature(Feature.VACANCY_WHY)
    matched_skills, matched_specializations, vacancy, user = row
    # Отвечаем на само сообщение с вакансией: во всплывающем окне лимит
    # 200 символов, и оно исчезает без следа.
    await callback.message.reply(
        build_vacancy_reason_text(
            matched_specializations or [],
            matched_skills or [],
            _caveats(vacancy, user),
        )
    )


@router.callback_query(F.data.startswith(VACANCY_REJECT_CALLBACK_PREFIX))
async def reject_vacancy(callback: CallbackQuery) -> None:
    vacancy_id = _vacancy_id(callback.data or "", VACANCY_REJECT_CALLBACK_PREFIX)
    if vacancy_id is None or callback.from_user is None:
        await callback.answer()
        return

    async with async_session_factory() as session:
        await session.execute(
            update(VacancyDispatchLog)
            .where(VacancyDispatchLog.vacancy_id == vacancy_id)
            .where(VacancyDispatchLog.user_tg_id == callback.from_user.id)
            .values(feedback=FEEDBACK_REJECTED, feedback_at=datetime.now(UTC))
        )
        await session.commit()

    observe_feature(Feature.VACANCY_REJECT)
    await callback.answer("Отмечено, учту")
    if isinstance(callback.message, Message):
        try:
            channel, url = await _source_of(vacancy_id)
            await callback.message.edit_reply_markup(
                reply_markup=get_vacancy_kb(
                    str(vacancy_id), rejected=True, source_channel=channel, source_url=url
                )
            )
        except Exception:
            logger.debug("Failed to update keyboard after rejection", exc_info=True)


@router.callback_query(F.data.startswith(VACANCY_UNDO_CALLBACK_PREFIX))
async def undo_rejection(callback: CallbackQuery) -> None:
    """Кнопки стоят рядом, промахи неизбежны — а сигнал нужен чистый."""
    vacancy_id = _vacancy_id(callback.data or "", VACANCY_UNDO_CALLBACK_PREFIX)
    if vacancy_id is None or callback.from_user is None:
        await callback.answer()
        return

    async with async_session_factory() as session:
        await session.execute(
            update(VacancyDispatchLog)
            .where(VacancyDispatchLog.vacancy_id == vacancy_id)
            .where(VacancyDispatchLog.user_tg_id == callback.from_user.id)
            .values(feedback=None, feedback_at=None)
        )
        await session.commit()

    observe_feature(Feature.VACANCY_UNDO)
    await callback.answer("Отметка снята")
    if isinstance(callback.message, Message):
        try:
            channel, url = await _source_of(vacancy_id)
            await callback.message.edit_reply_markup(
                reply_markup=get_vacancy_kb(str(vacancy_id), source_channel=channel, source_url=url)
            )
        except Exception:
            logger.debug("Failed to restore keyboard after undo", exc_info=True)
