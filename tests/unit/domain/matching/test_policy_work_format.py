from uuid import uuid4

from app.domain.matching.entities import MatchRejectionReason
from app.domain.matching.policy import evaluate_match
from app.domain.shared import WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode
from app.domain.vacancy.entities import Vacancy


def _build_user(work_format: WorkFormat | None, mode: FilterMode) -> User:
    return User.create(
        tg_id=1,
        cv_specializations_raw=["Backend"],
        cv_skills_raw=["Python"],
        cv_work_format=work_format,
        filter_work_format_mode=mode,
    )


def _build_vacancy(work_format: WorkFormat) -> Vacancy:
    return Vacancy.create(
        vacancy_id=uuid4(),
        text="Senior backend engineer (Python)",
        specializations_raw=["Backend"],
        skills_raw=["Python", "React"],
        mirror_chat_id=1,
        mirror_message_id=1,
        work_format=work_format,
    )


def test_strict_work_format_mismatch_rejected() -> None:
    user = _build_user(work_format=WorkFormat.REMOTE, mode=FilterMode.STRICT)
    vacancy = _build_vacancy(work_format=WorkFormat.ONSITE)

    decision = evaluate_match(vacancy=vacancy, user=user)

    assert decision.accepted is False
    assert decision.reason == MatchRejectionReason.FORMAT


def test_strict_work_format_undefined_vacancy_rejected() -> None:
    user = _build_user(work_format=WorkFormat.HYBRID, mode=FilterMode.STRICT)
    vacancy = _build_vacancy(work_format=WorkFormat.UNDEFINED)

    decision = evaluate_match(vacancy=vacancy, user=user)

    assert decision.accepted is False
    assert decision.reason == MatchRejectionReason.FORMAT


def test_soft_work_format_does_not_reject() -> None:
    user = _build_user(work_format=WorkFormat.REMOTE, mode=FilterMode.SOFT)
    vacancy = _build_vacancy(work_format=WorkFormat.ONSITE)

    decision = evaluate_match(vacancy=vacancy, user=user)

    assert decision.accepted is True
    assert decision.reason is None
