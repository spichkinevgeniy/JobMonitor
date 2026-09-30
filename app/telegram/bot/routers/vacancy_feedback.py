from uuid import UUID

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.application.ports.observability_port import Feature
from app.application.services.vacancy_feedback_service import (
    VacancyExplanation,
    VacancyFeedbackService,
)
from app.core.logger import get_app_logger
from app.domain.matching.entities import MatchRejectionReason
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


def _vacancy_id(data: str, prefix: str) -> UUID | None:
    try:
        return UUID(data.removeprefix(prefix))
    except ValueError:
        return None


def _caveats(explanation: VacancyExplanation) -> list[str]:
    """Пояснение к каждому фильтру, который пропустил вакансию из-за пустого поля."""
    lines: list[str] = []
    for reason in explanation.unchecked_filters:
        if reason is MatchRejectionReason.FORMAT and explanation.user_work_format:
            lines.append(build_reason_caveat_format(explanation.user_work_format))
        elif reason is MatchRejectionReason.GRADE:
            lines.append(build_reason_caveat_grade())
        elif reason is MatchRejectionReason.EXPERIENCE:
            lines.append(build_reason_caveat_experience())
        elif reason is MatchRejectionReason.SALARY:
            lines.append(build_reason_caveat_salary())
    return lines


@router.callback_query(F.data.startswith(VACANCY_WHY_CALLBACK_PREFIX))
async def explain_vacancy(
    callback: CallbackQuery, vacancy_feedback: VacancyFeedbackService
) -> None:
    vacancy_id = _vacancy_id(callback.data or "", VACANCY_WHY_CALLBACK_PREFIX)
    if vacancy_id is None or callback.from_user is None:
        await callback.answer()
        return

    explanation = await vacancy_feedback.explain(vacancy_id, callback.from_user.id)

    await callback.answer()
    if explanation is None or not isinstance(callback.message, Message):
        return

    observe_feature(Feature.VACANCY_WHY)
    # Отвечаем на само сообщение с вакансией: во всплывающем окне лимит
    # 200 символов, и оно исчезает без следа.
    await callback.message.reply(
        build_vacancy_reason_text(
            explanation.matched_specializations,
            explanation.matched_skills,
            _caveats(explanation),
        )
    )


@router.callback_query(F.data.startswith(VACANCY_REJECT_CALLBACK_PREFIX))
async def reject_vacancy(callback: CallbackQuery, vacancy_feedback: VacancyFeedbackService) -> None:
    vacancy_id = _vacancy_id(callback.data or "", VACANCY_REJECT_CALLBACK_PREFIX)
    if vacancy_id is None or callback.from_user is None:
        await callback.answer()
        return

    await vacancy_feedback.reject(vacancy_id, callback.from_user.id)

    observe_feature(Feature.VACANCY_REJECT)
    await callback.answer("Отмечено, учту")
    if isinstance(callback.message, Message):
        try:
            source = await vacancy_feedback.source_of(vacancy_id)
            await callback.message.edit_reply_markup(
                reply_markup=get_vacancy_kb(
                    str(vacancy_id),
                    rejected=True,
                    source_channel=source.channel,
                    source_url=source.url,
                )
            )
        except Exception:
            logger.debug("Failed to update keyboard after rejection", exc_info=True)


@router.callback_query(F.data.startswith(VACANCY_UNDO_CALLBACK_PREFIX))
async def undo_rejection(callback: CallbackQuery, vacancy_feedback: VacancyFeedbackService) -> None:
    """Кнопки стоят рядом, промахи неизбежны — а сигнал нужен чистый."""
    vacancy_id = _vacancy_id(callback.data or "", VACANCY_UNDO_CALLBACK_PREFIX)
    if vacancy_id is None or callback.from_user is None:
        await callback.answer()
        return

    await vacancy_feedback.undo_rejection(vacancy_id, callback.from_user.id)

    observe_feature(Feature.VACANCY_UNDO)
    await callback.answer("Отметка снята")
    if isinstance(callback.message, Message):
        try:
            source = await vacancy_feedback.source_of(vacancy_id)
            await callback.message.edit_reply_markup(
                reply_markup=get_vacancy_kb(
                    str(vacancy_id), source_channel=source.channel, source_url=source.url
                )
            )
        except Exception:
            logger.debug("Failed to restore keyboard after undo", exc_info=True)
