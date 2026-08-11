from copy import deepcopy

from app.domain.shared import WorkFormat, WorkFormats
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode


def test_legacy_writer_updates_collection() -> None:
    user = User.create(tg_id=1)

    user.set_legacy_work_format(WorkFormat.REMOTE, FilterMode.STRICT)

    assert user.cv_work_format is WorkFormat.REMOTE
    assert user.filter_work_format_mode is FilterMode.STRICT
    assert user.cv_work_formats == WorkFormats.from_values([WorkFormat.REMOTE])


def test_new_writer_projects_singleton_to_legacy_scalar() -> None:
    user = User.create(tg_id=1)

    user.set_work_formats(WorkFormats.from_values([WorkFormat.HYBRID]))

    assert user.cv_work_format is WorkFormat.HYBRID
    assert user.filter_work_format_mode is FilterMode.STRICT


def test_new_writer_projects_multiple_formats_to_legacy_any() -> None:
    user = User.create(tg_id=1)

    user.set_work_formats(WorkFormats.from_values([WorkFormat.REMOTE, WorkFormat.HYBRID]))

    assert user.cv_work_format is None
    assert user.filter_work_format_mode is FilterMode.SOFT
    assert user.effective_work_formats.items == {
        WorkFormat.REMOTE,
        WorkFormat.HYBRID,
    }


def test_legacy_writer_replaces_multiple_formats_with_singleton() -> None:
    user = User.create(tg_id=1)
    user.set_work_formats(WorkFormats.from_values([WorkFormat.REMOTE, WorkFormat.HYBRID]))

    user.set_legacy_work_format(WorkFormat.REMOTE, FilterMode.STRICT)

    assert user.cv_work_formats == WorkFormats.from_values([WorkFormat.REMOTE])


def test_unrelated_user_update_does_not_change_formats() -> None:
    user = User.create(tg_id=1)
    user.set_work_formats(WorkFormats.from_values([WorkFormat.REMOTE, WorkFormat.HYBRID]))
    expected = deepcopy(user.cv_work_formats)

    user.username = "new-name"

    assert user.cv_work_formats == expected
