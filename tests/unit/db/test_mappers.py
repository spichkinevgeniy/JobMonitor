from app.domain.shared import WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode
from app.infrastructure.db.mappers.user import user_from_model, user_to_model
from app.infrastructure.db.models import User as UserModel


def test_user_mapper_round_trip_preserves_skills() -> None:
    user = User.create(
        tg_id=123,
        username="alice",
        cv_text="resume text",
        cv_specializations_raw=["Backend"],
        cv_skills_raw=["Python", "React"],
        filter_salary_mode=FilterMode.SOFT,
        filter_work_format_mode=FilterMode.SOFT,
    )

    model = user_to_model(user)
    restored = user_from_model(model)

    assert sorted(model.cv_skills) == ["Python", "React"]
    assert sorted(item.value for item in restored.cv_skills.items) == ["Python", "React"]


def test_user_mapper_normalizes_undefined_work_format_to_any() -> None:
    model = UserModel(
        tg_id=123,
        username="alice",
        cv_text=None,
        cv_specializations=["Backend"],
        cv_skills=["Python"],
        cv_salary_amount=None,
        cv_salary_currency=None,
        filter_salary_mode=FilterMode.SOFT.value,
        cv_work_format=WorkFormat.UNDEFINED.value,
        filter_work_format_mode=FilterMode.STRICT.value,
        is_active=True,
    )

    restored = user_from_model(model)

    assert restored.cv_work_format is None
    assert restored.filter_work_format_mode == FilterMode.SOFT
