from uuid import uuid4

import pytest

from app.domain.matching.policy import evaluate_match
from app.domain.shared import WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode
from app.domain.vacancy.entities import Vacancy


def _vacancy(work_format: WorkFormat) -> Vacancy:
    return Vacancy.create(
        vacancy_id=uuid4(),
        text="vacancy",
        specializations_raw=["Backend"],
        skills_raw=["Python"],
        mirror_chat_id=1,
        mirror_message_id=1,
        work_format=work_format,
    )


@pytest.mark.parametrize(
    ("scalar", "mode"),
    [
        (WorkFormat.REMOTE, FilterMode.STRICT),
        (WorkFormat.REMOTE, FilterMode.SOFT),
        (None, FilterMode.SOFT),
        (WorkFormat.UNDEFINED, FilterMode.STRICT),
    ],
)
def test_backfilled_collection_preserves_legacy_matching(
    scalar: WorkFormat | None,
    mode: FilterMode,
) -> None:
    legacy = User.create(
        tg_id=1,
        cv_work_format=scalar,
        filter_work_format_mode=mode,
    )
    backfilled = User.create(
        tg_id=2,
        cv_work_format=legacy.cv_work_format,
        filter_work_format_mode=legacy.filter_work_format_mode,
        cv_work_formats_raw=(
            [legacy.cv_work_format.value]
            if legacy.filter_work_format_mode is FilterMode.STRICT
            and legacy.cv_work_format is not None
            else []
        ),
    )

    for vacancy_format in WorkFormat:
        assert evaluate_match(_vacancy(vacancy_format), legacy) == evaluate_match(
            _vacancy(vacancy_format),
            backfilled,
        )


def test_multiple_work_formats_accept_members_and_reject_others() -> None:
    user = User.create(
        tg_id=1,
        cv_work_formats_raw=[WorkFormat.REMOTE.value, WorkFormat.HYBRID.value],
    )

    assert evaluate_match(_vacancy(WorkFormat.REMOTE), user).accepted is True
    assert evaluate_match(_vacancy(WorkFormat.HYBRID), user).accepted is True
    assert evaluate_match(_vacancy(WorkFormat.ONSITE), user).accepted is False
    # «Не указан» не равно «не подходит»: правило пришло из main и одинаково
    # работает и для одного формата, и для нескольких.
    assert evaluate_match(_vacancy(WorkFormat.UNDEFINED), user).accepted is True
