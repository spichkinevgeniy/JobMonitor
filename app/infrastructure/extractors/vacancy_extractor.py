import re

from app.application.dto import OutVacancyParse
from app.application.ports.llm_port import IVacancyLLMExtractor
from app.core.logger import get_app_logger
from app.infrastructure.llm import get_vacancy_parse_agent
from app.infrastructure.llm_runtime import run_with_llm_retry

logger = get_app_logger(__name__)

_WHITESPACE = re.compile(r"\s+")
MIN_EVIDENCE_LENGTH = 3

# Навыки, название которых обязано звучать в самой цитате.
#
# Цитата из текста — ещё не обоснование: на проде Node.js подтверждался
# фрагментами «сервисы на базе Spring» и «backend платформы», то есть
# модель выводила его из соседних понятий. Здесь перечислены технологии,
# у которых есть собственное имя; зонтичные навыки вроде DevOps и QA
# Automation в список не входят — их законно подтверждают инструменты.
_SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Node.js": ("node",),
    "React": ("react", "реакт"),
    "Vue": ("vue",),
    "Angular": ("angular",),
    "TypeScript": ("typescript", "ts"),
    "Python": ("python", "питон"),
    "Java/Scala": ("java", "scala", "kotlin", "spring", "джава"),
    "C#": ("c#", ".net", "asp.net", "шарп"),
    "Go": ("go", "golang"),
    "PHP": ("php", "laravel", "symfony"),
    "Ruby": ("ruby", "rails"),
    "Rust": ("rust",),
    "C++": ("c++", "cpp"),
    "Unity": ("unity",),
    "Unreal Engine": ("unreal", "ue4", "ue5"),
    "Flutter": ("flutter", "dart"),
    "Android": ("android", "андроид"),
    "iOS": ("ios", "swift"),
    "React Native": ("react native",),
    "SQL": ("sql",),
    "Figma": ("figma", "фигма"),
}


def _normalized(value: str) -> str:
    """Приводит к виду, в котором цитату можно искать в тексте.

    Модель переносит строки и меняет регистр даже когда просят копировать
    символ в символ, и на этом честные цитаты отсеивались бы наравне с
    выдуманными.
    """
    return _WHITESPACE.sub(" ", value).strip().lower()


def drop_unsupported_skills(parsed: OutVacancyParse, text: str) -> int:
    """Убирает навыки, цитату которых не найти в тексте вакансии.

    Промпт просит не выдумывать навыки с самого начала, и это не работает:
    на проде 41% меток Node.js стояло на вакансиях, где слова `node` нет
    вовсе. Просьбу модель нарушает молча, а подстроку проверяет код.
    """
    haystack = _normalized(text)
    kept = []
    dropped = []
    for item in parsed.skills:
        evidence = _normalized(item.evidence)
        if not evidence or evidence not in haystack:
            dropped.append(item.skill.value)
            continue

        aliases = _SKILL_ALIASES.get(item.skill.value)
        if aliases is not None:
            # Имя технологии в цитате — проверка сильная, и длина уже не нужна:
            # «Go» и «C#» короче любого разумного минимума, но подтверждают
            # навык не хуже развёрнутой фразы.
            if not any(alias in evidence for alias in aliases):
                dropped.append(item.skill.value)
                continue
        elif len(evidence) < MIN_EVIDENCE_LENGTH:
            # У зонтичных навыков имени в тексте нет, и от мусорной цитаты
            # защищает только длина.
            dropped.append(item.skill.value)
            continue

        kept.append(item)

    if dropped:
        logger.info("Vacancy skills without evidence dropped: %s", ", ".join(dropped))
    parsed.skills = kept
    return len(dropped)


class GoogleVacancyLLMExtractor(IVacancyLLMExtractor):
    def __init__(self) -> None:
        self._agent = get_vacancy_parse_agent()

    async def parse_vacancy(self, text: str) -> OutVacancyParse:
        result = await run_with_llm_retry(
            "vacancy_parse",
            lambda: self._agent.run(
                user_prompt=(
                    f"Проанализируй текст и сначала определи, является ли он вакансией:\n{text}"
                ),
                metadata={"pipeline": "vacancy_ingest"},
            ),
        )
        parsed = result.output
        drop_unsupported_skills(parsed, text)
        return parsed
