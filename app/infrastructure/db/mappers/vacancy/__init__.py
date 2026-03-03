from app.domain.shared.value_objects import (
    PrimaryLanguages,
    Salary,
    Specializations,
    TechStack,
    WorkFormat,
)
from app.domain.vacancy.entities import Vacancy
from app.domain.vacancy.value_objects import ContentHash, VacancyId
from app.infrastructure.db.models import Vacancy as VacancyModel


def vacancy_to_model(vacancy: Vacancy) -> VacancyModel:
    return VacancyModel(
        id=vacancy.id.value,
        text=vacancy.text,
        specializations=[s.value for s in vacancy.specializations.items],
        primary_languages=[lang.value for lang in vacancy.primary_languages.items],
        tech_stack=list(vacancy.tech_stack.items),
        min_experience_months=vacancy.min_experience_months,
        mirror_chat_id=vacancy.mirror_chat_id,
        mirror_message_id=vacancy.mirror_message_id,
        content_hash=vacancy.content_hash.value,
        salary_amount=vacancy.salary.amount,
        salary_currency=vacancy.salary.currency.value if vacancy.salary.currency else None,
        work_format=vacancy.work_format.value if vacancy.work_format else None,
        created_at=vacancy.created_at,
        is_active=vacancy.is_active,
    )


def apply_vacancy(model: VacancyModel, vacancy: Vacancy) -> None:
    model.text = vacancy.text
    model.specializations = [s.value for s in vacancy.specializations.items]
    model.primary_languages = [lang.value for lang in vacancy.primary_languages.items]
    model.tech_stack = list(vacancy.tech_stack.items)
    model.min_experience_months = vacancy.min_experience_months
    model.mirror_chat_id = vacancy.mirror_chat_id
    model.mirror_message_id = vacancy.mirror_message_id
    model.content_hash = vacancy.content_hash.value
    model.salary_amount = vacancy.salary.amount
    model.salary_currency = vacancy.salary.currency.value if vacancy.salary.currency else None
    model.work_format = vacancy.work_format.value
    model.is_active = vacancy.is_active


def vacancy_from_model(model: VacancyModel) -> Vacancy:
    return Vacancy(
        id=VacancyId(model.id),
        text=model.text,
        specializations=Specializations.from_strs(model.specializations or []),
        primary_languages=PrimaryLanguages.from_strs(model.primary_languages or []),
        tech_stack=TechStack.create(model.tech_stack or []),
        min_experience_months=model.min_experience_months,
        mirror_chat_id=model.mirror_chat_id,
        mirror_message_id=model.mirror_message_id,
        salary=Salary.create(model.salary_amount, model.salary_currency),
        work_format=WorkFormat(model.work_format) if model.work_format else WorkFormat.UNDEFINED,
        content_hash=ContentHash(model.content_hash),
        created_at=model.created_at,
        is_active=model.is_active,
    )
