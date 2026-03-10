from functools import lru_cache

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, Model
from pydantic_ai.providers.google import GoogleProvider

from app.application.dto import OutResumeParse, OutResumeSalaryParse, OutVacancyParse
from app.core.config import config
from app.domain.shared.value_objects import SkillType


def get_google_model() -> Model:
    provider = GoogleProvider(api_key=config.GOOGLE_API_KEY)
    return GoogleModel(config.GOOGLE_MODEL, provider=provider)


@lru_cache(maxsize=1)
def get_vacancy_parse_agent() -> Agent[None, OutVacancyParse]:
    allowed_skills = ", ".join(skill.value for skill in SkillType)
    system_prompt = (
        "Ты — строгий фильтр IT-вакансий. Ошибка классификации опаснее в сторону false positive, "
        "чем false negative.\n"
        "Сначала реши только is_vacancy.\n"
        "Ставь is_vacancy=true только если текст явно является объявлением о найме "
        "или поиске исполнителя "
        "со стороны работодателя или заказчика.\n"
        "Для is_vacancy=true должны одновременно выполняться оба условия:\n"
        "1. Есть явная роль, позиция или запрос на конкретного специалиста.\n"
        "2. Есть хотя бы один из признаков найма: требования, обязанности, условия работы, "
        "зарплата, "
        "формат работы, описание компании, процесс отклика, контакт для кандидата.\n\n"
        "Ставь is_vacancy=false в любом из случаев:\n"
        "- это резюме, профиль кандидата, самопрезентация или описание собственных навыков;\n"
        "- это предложение услуг, поиск проектов, фриланс-объявление от исполнителя, "
        "а не вакансия от "
        "работодателя;\n"
        "- это список технологий, стек, опыт, портфолио или достижения "
        "без явного контекста найма;\n"
        "- текст написан от первого лица и продает самого автора: 'я', 'мой опыт', 'создал', "
        "'реализовывал', 'готов', 'всегда на связи', 'предоставлю примеры работ';\n"
        "- есть маркеры профиля кандидата или услуги: 'опыт работы', 'стек', 'инструменты', "
        "'портфолио', 'зарплатные ожидания', 'почасовая оплата', "
        "'от ... за проект', 'контакты: @...';\n"
        "- нет явного работодателя или явного запроса на найм;\n"
        "- есть сомнение, это вакансия или профиль кандидата.\n"
        "Если есть смешанные сигналы, выбирай is_vacancy=false.\n"
        "Только после решения по is_vacancy извлекай поля.\n\n"
        "Если это вакансия, извлеки:\n"
        "1. specializations только из фиксированного списка.\n"
        f"2. skills только из SkillType: {allowed_skills}.\n"
        "   - Извлекай только явные упоминания.\n"
        "   - React и Vue сохраняй как отдельные skills.\n"
        "   - Не придумывай skills вне списка.\n"
        "3. salary: извлекай только зарплату в RUB; если указан диапазон, бери минимум. "
        "Если валюта другая или надежно определить RUB нельзя, верни null.\n"
        "4. work_format: REMOTE, HYBRID, ONSITE или UNDEFINED.\n"
    )

    return Agent[None, OutVacancyParse](
        model=get_google_model(),
        system_prompt=system_prompt,
        output_type=OutVacancyParse,
        model_settings={"temperature": 0.0},
        name="vacancy_parser_agent",
        metadata={"agent_type": "vacancy_parser"},
    )


@lru_cache(maxsize=1)
def get_resume_parse_agent() -> Agent[None, OutResumeParse]:
    allowed_skills = ", ".join(skill.value for skill in SkillType)
    system_prompt = (
        "Ты — эксперт по разбору технических резюме.\n"
        "Преобразуй резюме в структурированные поля.\n\n"
        "Правила:\n"
        "1. is_resume=true только для резюме и профилей кандидата.\n"
        "2. specializations выбирай только из фиксированного списка.\n"
        f"3. skills выбирай только из SkillType: {allowed_skills}.\n"
        "   - Извлекай только явные упоминания.\n"
        "   - React и Vue сохраняй как отдельные skills.\n"
        "   - Не придумывай skills вне списка.\n"
        "4. salary — желаемая зарплата только в RUB; если указан диапазон, бери минимум. "
        "Если валюта другая или надежно определить RUB нельзя, верни null.\n"
        "5. work_format — одно из REMOTE, HYBRID, ONSITE, UNDEFINED.\n"
        "6. full_relevant_text_from_resume сохраняй без искажений.\n"
    )

    return Agent[None, OutResumeParse](
        model=get_google_model(),
        system_prompt=system_prompt,
        output_type=OutResumeParse,
        model_settings={"temperature": 0.0},
        name="resume_parser_agent",
        metadata={"agent_type": "resume_parser"},
    )


@lru_cache(maxsize=1)
def get_resume_salary_agent() -> Agent[None, OutResumeSalaryParse]:
    system_prompt = (
        "Извлеки из резюме только информацию о зарплате.\n"
        "Верни amount, currency и короткий evidence-фрагмент.\n"
        "Извлекай только зарплату в RUB. Если указан диапазон, бери минимум. "
        "Если валюта другая, зарплата не указана или RUB нельзя надежно определить, верни null.\n"
        "Ничего не придумывай."
    )

    return Agent[None, OutResumeSalaryParse](
        model=get_google_model(),
        system_prompt=system_prompt,
        output_type=OutResumeSalaryParse,
        model_settings={"temperature": 0.0},
        name="resume_salary_agent",
        metadata={"agent_type": "resume_salary"},
    )
