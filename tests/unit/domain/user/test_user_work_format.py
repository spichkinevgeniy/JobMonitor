from app.domain.shared import WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode


def test_user_create_normalizes_undefined_work_format_to_any() -> None:
    user = User.create(
        tg_id=1,
        cv_work_format=WorkFormat.UNDEFINED,
        filter_work_format_mode=FilterMode.STRICT,
    )

    assert user.cv_work_format is None
    assert user.filter_work_format_mode == FilterMode.SOFT
