from dataclasses import dataclass

from app.domain.shared.value_objects import (
    PrimaryLanguages,
    Salary,
    Specializations,
    TechStack,
    WorkFormat,
)
from app.domain.user.value_objects import FilterMode, UserId


@dataclass(slots=True)
class User:
    tg_id: UserId
    username: str | None
    cv_text: str | None

    cv_specializations: Specializations
    cv_primary_languages: PrimaryLanguages
    cv_tech_stack: TechStack | None

    cv_experience_months: int | None
    filter_experience_min_months: int | None

    cv_salary: Salary | None
    filter_salary_mode: FilterMode

    cv_work_format: WorkFormat | None
    filter_work_format_mode: FilterMode

    is_active: bool = True

    @classmethod
    def create(
        cls,
        tg_id: int,
        username: str | None = None,
        cv_text: str | None = None,
        cv_specializations_raw: list[str] | None = None,
        cv_primary_languages_raw: list[str] | None = None,
        cv_tech_stack_raw: list[str] | None = None,
        cv_experience_months: int | None = None,
        filter_experience_min_months: int | None = None,
        cv_salary_amount: int | None = None,
        cv_salary_currency: str | None = None,
        filter_salary_mode: FilterMode | str | None = None,
        cv_work_format: WorkFormat | str | None = None,
        filter_work_format_mode: FilterMode | str | None = None,
        is_active: bool = True,
    ) -> "User":
        specs = Specializations.from_strs(cv_specializations_raw or [])
        langs = PrimaryLanguages.from_strs(cv_primary_languages_raw or [])
        stack = None
        if cv_tech_stack_raw is not None:
            created_stack = TechStack.create(cv_tech_stack_raw)
            if created_stack.items:
                stack = created_stack

        experience_months = None if cv_experience_months is None else max(0, cv_experience_months)
        experience_min_months = cls._normalize_experience_min_months(filter_experience_min_months)
        has_salary = cv_salary_amount is not None or bool(
            cv_salary_currency and cv_salary_currency.strip()
        )
        salary = Salary.create(cv_salary_amount, cv_salary_currency) if has_salary else None
        salary_mode = cls._normalize_mode(filter_salary_mode)
        if salary is None:
            salary_mode = FilterMode.SOFT

        work_format = cls._normalize_work_format(cv_work_format)
        work_format_mode = cls._normalize_mode(filter_work_format_mode)
        if work_format is None:
            work_format_mode = FilterMode.SOFT

        return cls(
            tg_id=UserId(tg_id),
            username=username,
            cv_text=cv_text,
            cv_specializations=specs,
            cv_primary_languages=langs,
            cv_tech_stack=stack,
            cv_experience_months=experience_months,
            filter_experience_min_months=experience_min_months,
            cv_salary=salary,
            filter_salary_mode=salary_mode,
            cv_work_format=work_format,
            filter_work_format_mode=work_format_mode,
            is_active=is_active,
        )

    @staticmethod
    def _normalize_mode(raw: FilterMode | str | None) -> FilterMode:
        if isinstance(raw, FilterMode):
            return raw
        if raw is None:
            return FilterMode.SOFT
        if isinstance(raw, str):
            cleaned = raw.strip()
            if not cleaned:
                return FilterMode.SOFT
            return FilterMode(cleaned.upper())
        return FilterMode.SOFT

    @staticmethod
    def _normalize_work_format(raw: WorkFormat | str | None) -> WorkFormat | None:
        if isinstance(raw, WorkFormat):
            return raw
        if raw is None:
            return None
        if isinstance(raw, str):
            cleaned = raw.strip()
            if not cleaned:
                return None
            return WorkFormat(cleaned.upper())
        return None

    @staticmethod
    def _normalize_experience_min_months(raw: int | None) -> int | None:
        allowed = {12, 36, 60}
        if raw in allowed:
            return raw
        return None
