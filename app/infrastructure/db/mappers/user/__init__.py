from app.domain.shared.value_objects import (
    PrimaryLanguages as UserPrimaryLanguages,
)
from app.domain.shared.value_objects import (
    Salary as UserSalary,
)
from app.domain.shared.value_objects import (
    Specializations as UserSpecializations,
)
from app.domain.shared.value_objects import (
    TechStack as UserTechStack,
)
from app.domain.shared.value_objects import (
    WorkFormat as UserWorkFormat,
)
from app.domain.user.entities import User
from app.domain.user.value_objects import (
    FilterMode,
    UserId,
)
from app.infrastructure.db.models import User as UserModel


def user_to_model(user: User) -> UserModel:
    return UserModel(
        tg_id=user.tg_id.value,
        username=user.username,
        cv_text=user.cv_text,
        cv_specializations=[item.value for item in user.cv_specializations.items],
        cv_primary_languages=[item.value for item in user.cv_primary_languages.items],
        cv_tech_stack=list(user.cv_tech_stack.items) if user.cv_tech_stack else None,
        cv_experience_months=user.cv_experience_months,
        filter_experience_min_months=user.filter_experience_min_months,
        cv_salary_amount=user.cv_salary.amount if user.cv_salary else None,
        cv_salary_currency=(
            user.cv_salary.currency.value if user.cv_salary and user.cv_salary.currency else None
        ),
        filter_salary_mode=user.filter_salary_mode.value,
        cv_work_format=user.cv_work_format.value if user.cv_work_format else None,
        filter_work_format_mode=user.filter_work_format_mode.value,
        is_active=user.is_active,
    )


def apply_user(model: UserModel, user: User) -> None:
    model.username = user.username
    model.cv_text = user.cv_text
    model.cv_specializations = [item.value for item in user.cv_specializations.items]
    model.cv_primary_languages = [item.value for item in user.cv_primary_languages.items]
    model.cv_tech_stack = list(user.cv_tech_stack.items) if user.cv_tech_stack else None
    model.cv_experience_months = user.cv_experience_months
    model.filter_experience_min_months = user.filter_experience_min_months
    model.cv_salary_amount = user.cv_salary.amount if user.cv_salary else None
    model.cv_salary_currency = (
        user.cv_salary.currency.value if user.cv_salary and user.cv_salary.currency else None
    )
    model.filter_salary_mode = user.filter_salary_mode.value
    model.cv_work_format = user.cv_work_format.value if user.cv_work_format else None
    model.filter_work_format_mode = user.filter_work_format_mode.value
    model.is_active = user.is_active


def user_from_model(model: UserModel) -> User:
    tech_stack = None
    if model.cv_tech_stack:
        created_stack = UserTechStack.create(model.cv_tech_stack)
        if created_stack.items:
            tech_stack = created_stack

    has_salary = model.cv_salary_amount is not None or bool(
        model.cv_salary_currency and model.cv_salary_currency.strip()
    )
    salary = (
        UserSalary.create(model.cv_salary_amount, model.cv_salary_currency) if has_salary else None
    )

    work_format = UserWorkFormat(model.cv_work_format) if model.cv_work_format else None
    filter_experience_min_months = (
        model.filter_experience_min_months
        if model.filter_experience_min_months in {12, 36, 60}
        else None
    )

    return User(
        tg_id=UserId(model.tg_id),
        username=model.username,
        cv_text=model.cv_text,
        cv_specializations=UserSpecializations.from_strs(model.cv_specializations or []),
        cv_primary_languages=UserPrimaryLanguages.from_strs(model.cv_primary_languages or []),
        cv_tech_stack=tech_stack,
        cv_experience_months=model.cv_experience_months,
        filter_experience_min_months=filter_experience_min_months,
        cv_salary=salary,
        filter_salary_mode=(
            FilterMode(model.filter_salary_mode) if model.filter_salary_mode else FilterMode.SOFT
        ),
        cv_work_format=work_format,
        filter_work_format_mode=(
            FilterMode(model.filter_work_format_mode)
            if model.filter_work_format_mode
            else FilterMode.SOFT
        ),
        is_active=model.is_active,
    )
