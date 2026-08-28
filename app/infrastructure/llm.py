from functools import lru_cache

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from app.application.dto import OutResumeParse, OutResumeSalaryParse, OutVacancyParse
from app.core.config import config
from app.domain.shared.value_objects import (
    CompanyType,
    ExperienceLevel,
    Grade,
    SkillType,
    SpecializationType,
)


@lru_cache(maxsize=1)
def get_openrouter_model() -> Model:
    provider = OpenRouterProvider(
        api_key=config.OPENROUTER_API_KEY,
        app_title=config.OPENROUTER_APP_TITLE,
    )
    return OpenRouterModel(config.OPENROUTER_MODEL, provider=provider)


# OpenRouter резервирует кредиты под максимум модели, а не под фактический
# ответ: без этого лимита каждый вызов требовал запаса на 65535 токенов и
# отбивался с 402, хотя тратил около сотни. Замер на реальных данных —
# 228 токенов в худшем случае, так что запас здесь почти двадцатикратный.
MAX_OUTPUT_TOKENS = 4096


@lru_cache(maxsize=1)
def get_vacancy_parse_agent() -> Agent[None, OutVacancyParse]:
    allowed_specializations = ", ".join(item.value for item in SpecializationType)
    allowed_skills = ", ".join(skill.value for skill in SkillType)
    allowed_grades = ", ".join(grade.value for grade in Grade)
    allowed_experience_levels = ", ".join(level.value for level in ExperienceLevel)
    allowed_company_types = ", ".join(item.value for item in CompanyType)
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
        "- это подборка, дайджест, список из нескольких вакансий, нескольких ролей или нескольких "
        "компаний; если в одном тексте больше одной вакансии и нет одной доминирующей роли, это "
        "не одна вакансия;\n"
        "- нет явного работодателя или явного запроса на найм;\n"
        "- есть сомнение, это вакансия или профиль кандидата.\n"
        "Если есть смешанные сигналы, выбирай is_vacancy=false.\n"
        "Только после решения по is_vacancy извлекай поля.\n\n"
        "Если это вакансия, извлеки:\n"
        f"1. specializations только из списка: {allowed_specializations}.\n"
        "   - Обычно хватает одной специализации: выбирай ту, к которой относится основная роль.\n"
        "   - Data Science / ML ставь, когда роль про обучение и применение моделей.\n"
        "   - Analytics ставь, когда роль про подготовку данных, витрины, отчетность и BI, "
        "включая Data Engineer и ETL-инженера.\n"
        "   - Infrastructure & DevOps ставь только для инфраструктурных ролей, а не для "
        "backend-вакансий, где упомянуты Docker или CI/CD.\n"
        "   - UI/UX & Product Design ставь для ролей про дизайн интерфейсов, прототипирование, "
        "UX-исследования и продуктовый дизайн. Не ставь Frontend только из-за упоминания Figma "
        "или макетов в вакансии верстальщика/frontend-разработчика — там дизайн не основная роль.\n"
        "   - Не придумывай значения вне списка.\n"
        f"2. skills только из SkillType: {allowed_skills}.\n"
        "   - Извлекай только skills, которые определяют саму вакансию: основную роль, основной "
        "стек или ключевую предметную область.\n"
        "   - Ориентируйся на смысл вакансии, а не на количество упоминаний. Напримре, Если вакансия по "
        "смыслу на Go-разработчика, а Python указан как дополнительный плюс или смежное "
        "требование, оставляй Go и не добавляй Python.\n"
        "   - Не добавляй skills из разделов `будет плюсом`, `nice to have`, дополнительных "
        "требований, бонусных знаний, смежных инструментов или второстепенных задач.\n"
        "   - SQL указывай только если работа с данными и есть суть роли: аналитика, "
        "отчетность, витрины, DWH, ETL. Не указывай SQL, если это обычная часть "
        "backend-стека: работа с базой, ORM, миграции, запросы из приложения.\n"
        "   - Data Engineering указывай для ролей про пайплайны данных, ETL/ELT, DWH и "
        "оркестрацию, а не для аналитиков отчетности и не для ML-инженеров.\n"
        "   - Figma/Prototyping/UX Research/Design Systems/Interaction Design указывай только "
        "для дизайнерских вакансий, а не когда Figma просто упомянута как источник макетов для "
        "frontend-разработчика.\n"
        "   - Максимум 3 skills. Если есть сомнение, выбирай меньше.\n"
        "   - Не придумывай skills вне списка.\n"
        "3. salary_amount: число в рублях без пробелов и знаков валюты; если указан диапазон, "
        "бери минимум; 300к трактуй как 300000. salary_currency ставь RUB, когда сумма найдена. "
        "Если валюта другая или надежно определить RUB нельзя, верни null в обоих полях.\n"
        f"4. grade: только одно значение из {allowed_grades}. "
        "Определи уровень вакансии по названию роли и формулировкам требований. "
        "Если уровень не ясен, верни UNDEFINED.\n"
        f"5. experience_level: только одно значение из {allowed_experience_levels}. "
        "Ориентируйся на требуемый коммерческий опыт. Если опыт не указан или неоднозначен, верни UNDEFINED.\n"
        "6. work_format: REMOTE, HYBRID, ONSITE или UNDEFINED.\n"
        f"7. company_type: только одно значение из {allowed_company_types}.\n"
        "   - PRODUCT: текст от первого лица про свой продукт/сервис ('наш продукт', "
        "'мы разрабатываем'), названа прямая компания-бренд без посредников, есть упоминание "
        "собственных пользователей или метрик продукта.\n"
        "   - OUTSTAFF: 'для нашего клиента', 'клиентский проект', 'у одного из наших клиентов', "
        "явное упоминание модели аутстаффа/аутсорса, смена проектов, либо это репост от "
        "кадрового агентства ('вакансия от агентства', 'не является прямым работодателем').\n"
        "   - STARTUP: 'молодая команда', 'стартап', 'один из первых разработчиков', "
        "упоминание раунда/инвестиций/опционов, маленькая явно названная команда.\n"
        "   - PROJECT_WORK: сдельная оплата, оплата по факту выполнения задачи, разовая задача, "
        "ГПХ (не трудоустройство), нужен исполнитель на конкретную задачу без речи о постоянной "
        "позиции.\n"
        "   - UNDEFINED: нет ни одного из перечисленных признаков — просто стек, требования и "
        "зарплата без контекста о компании или формате занятости.\n"
    )

    return Agent[None, OutVacancyParse](
        model=get_openrouter_model(),
        system_prompt=system_prompt,
        output_type=OutVacancyParse,
        model_settings={"temperature": 0.0, "max_tokens": MAX_OUTPUT_TOKENS},
        name="vacancy_parser_agent",
        metadata={"agent_type": "vacancy_parser"},
    )


@lru_cache(maxsize=1)
def get_resume_parse_agent() -> Agent[None, OutResumeParse]:
    allowed_specializations = ", ".join(item.value for item in SpecializationType)
    allowed_skills = ", ".join(skill.value for skill in SkillType)
    allowed_grades = ", ".join(grade.value for grade in Grade)
    allowed_experience_levels = ", ".join(level.value for level in ExperienceLevel)
    system_prompt = (
        "Ты — эксперт по разбору технических резюме.\n"
        "Преобразуй резюме в структурированные поля.\n\n"
        "Правила:\n"
        "1. is_resume=true только для резюме и профилей кандидата.\n"
        "1a. Прежде чем выбирать specializations и skills, определи реальную профессию "
        "кандидата по его должностям и опыту. Если человек по факту НЕ разработчик/инженер и "
        "НЕ UI/UX-дизайнер (например маркетолог, менеджер, аналитик без кода, HR), "
        "specializations и skills должны остаться ПУСТЫМИ — даже если в тексте упоминаются "
        "технические слова или платформы (iOS, Android, React и т.п.) в контексте его "
        "нетехнической работы (управление проектом и т.д. — это не значит, что он их "
        "разрабатывал). Если человек по факту UI/UX \\ Product дизайнер — ему можно ставить "
        "UI/UX & Product Design, но не Frontend/Backend/Mobile только потому что он в описании "
        "задач упоминает платформы, для которых дизайнил интерфейсы.\n"
        f"2. specializations выбирай только из списка: {allowed_specializations}. "
        "Максимум 3 специализации.\n"
        "   - Определи основную специализацию по желаемой должности, названию последних ролей "
        "и подтвержденному коммерческому опыту.\n"
        "   - Сильные сигналы: заголовок резюме, блок 'Желаемая должность', названия реальных "
        "должностей, многократно повторяющиеся обязанности.\n"
        "   - Слабые сигналы: 'интересно развиваться', 'хочу изучать', 'ожидания', смежные "
        "инструменты, разовые задачи в проекте.\n"
        "   - Не добавляй специализацию только по смежному стеку или карьерному интересу.\n"
        "   - Не ставь Data Science / ML только из-за RAG, LLM, embeddings, vector search, "
        "Whisper, AI agents, evaluation или работы с мультимодальными данными, если кандидат "
        "по роли является backend-разработчиком и не описывает себя как ML engineer / "
        "data scientist.\n"
        "   - Не ставь Infrastructure & DevOps только из-за Docker, Linux, Nginx, CI/CD, SSH, "
        "Bash, reverse proxy или деплойных задач, если это обычный стек backend-разработчика, "
        "а не основная инфраструктурная роль.\n"
        "   - UI/UX & Product Design ставь только если желаемая должность или последние роли "
        "явно про дизайн интерфейсов/продукта, а не про разработку.\n"
        "   - Если есть сомнение, выбирай меньше специализаций.\n"
        "   - Для каждой специализации укажи evidence — короткую дословную цитату из резюме, "
        "которая доказывает именно инженерную/разработческую роль кандидата. Если не можешь "
        "найти такую цитату — не добавляй эту специализацию вообще.\n"
        f"3. skills выбирай только из SkillType: {allowed_skills}. "
        "Максимум 6 skills, выбирай самые весомые и часто встречающиеся, если кандидатов "
        "на попадание в список больше.\n"
        "   - Извлекай только явные упоминания.\n"
        "   - Не придумывай skills вне списка.\n"
        "   - Machine Learning указывай только если есть явный опыт именно в ML, а не просто "
        "использование LLM/RAG как прикладного backend-инструмента.\n"
        "   - NLP можно указывать, если в резюме явно есть работа с LLM, текстом, retrieval "
        "или NLP-задачами.\n"
        "   - Computer Vision не указывай только по упоминанию видео, аудио или Whisper; "
        "нужны явные CV-задачи как часть работы кандидата.\n"
        "   - DevOps и System Administration не указывай только по Docker/Linux/Nginx/SSH, "
        "если это вторичные навыки backend-инженера.\n"
        "   - Data Analysis не выводи только из наличия SQL.\n"
        "   - SQL указывай только если работа с данными была сутью роли кандидата: аналитика, "
        "отчетность, витрины, DWH, ETL. Не указывай SQL, если это обычная работа "
        "backend-разработчика с базой через ORM и запросы из приложения.\n"
        "   - Data Engineering указывай при явном опыте с пайплайнами данных, ETL/ELT, DWH или "
        "оркестрацией (Airflow и аналоги).\n"
        "   - Figma/Prototyping/UX Research/Design Systems/Interaction Design указывай только "
        "для UI/UX \\ Product дизайнеров, не для разработчиков, которые просто смотрят макеты в "
        "Figma.\n"
        "   - Если есть сомнение, выбирай меньше skills.\n"
        "   - Для каждого skill укажи evidence — короткую дословную цитату из резюме, которая "
        "явно упоминает этот навык. Если не можешь процитировать текст — не добавляй этот "
        "skill вообще, это признак, что ты его придумал.\n"
        "4. salary_amount — желаемая зарплата числом в рублях, без пробелов и знаков валюты; "
        "если указан диапазон, бери минимум; 300к трактуй как 300000. salary_currency ставь RUB, "
        "когда сумма найдена. Если валюта другая или надежно определить RUB нельзя, верни null "
        "в обоих полях.\n"
        f"5. grade — только одно значение из {allowed_grades}. "
        "Ориентируйся на последний подтвержденный уровень кандидата. Если уровень не ясен, верни UNDEFINED.\n"
        f"6. experience_level — только одно значение из {allowed_experience_levels}. "
        "Ориентируйся на подтвержденный коммерческий опыт. Если опыт не ясен, верни UNDEFINED.\n"
        "7. work_format — одно из REMOTE, HYBRID, ONSITE, UNDEFINED.\n"
    )

    return Agent[None, OutResumeParse](
        model=get_openrouter_model(),
        system_prompt=system_prompt,
        output_type=OutResumeParse,
        model_settings={"temperature": 0.0, "max_tokens": MAX_OUTPUT_TOKENS},
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
        model=get_openrouter_model(),
        system_prompt=system_prompt,
        output_type=OutResumeSalaryParse,
        model_settings={"temperature": 0.0, "max_tokens": MAX_OUTPUT_TOKENS},
        name="resume_salary_agent",
        metadata={"agent_type": "resume_salary"},
    )
