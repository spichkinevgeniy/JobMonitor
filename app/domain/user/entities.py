from dataclasses import dataclass

from app.domain.shared.value_objects import Salary, Skills, Specializations, WorkFormat
from app.domain.user.value_objects import FilterMode, UserId


@dataclass(slots=True)
class User:
    tg_id: UserId
    username: str | None
    cv_text: str | None

    cv_specializations: Specializations
    cv_skills: Skills

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
        cv_skills_raw: list[str] | None = None,
        cv_salary_amount: int | None = None,
        cv_salary_currency: str | None = None,
        filter_salary_mode: FilterMode | str | None = None,
        cv_work_format: WorkFormat | str | None = None,
        filter_work_format_mode: FilterMode | str | None = None,
        is_active: bool = True,
    ) -> "User":
        specs = Specializations.from_strs(cv_specializations_raw or [])
        skills = Skills.from_strs(cv_skills_raw or [])

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
            cv_skills=skills,
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
            return None if raw == WorkFormat.UNDEFINED else raw
        if raw is None:
            return None
        if isinstance(raw, str):
            cleaned = raw.strip()
            if not cleaned:
                return None
            normalized = WorkFormat(cleaned.upper())
            return None if normalized == WorkFormat.UNDEFINED else normalized
        return None
