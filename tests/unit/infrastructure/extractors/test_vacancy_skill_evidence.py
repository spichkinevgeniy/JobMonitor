"""Навык вакансии принимается только с опорой в её тексте.

Промпт с самого начала просил не выдумывать навыки, и это не работало:
на проде 41% меток Node.js стояло на вакансиях, где слова «node» нет
вовсе — Java, Go, Ruby, PHP. Половина всех отметок «не подходит» пришла
именно оттуда. Просьбу модель нарушает молча, подстроку проверяет код.
"""

from app.application.dto import OutVacancyParse
from app.application.dto.resume_dto import SkillWithEvidence
from app.domain.shared.value_objects import SkillType
from app.infrastructure.extractors.vacancy_extractor import drop_unsupported_skills

JAVA_VACANCY = (
    "Java-разработчик (Middle/Senior). Разрабатывать и поддерживать "
    "сервисы на базе Spring. Вилка 180 000 - 250 000 рублей. GitLab CI."
)


def _parsed(*skills: SkillWithEvidence) -> OutVacancyParse:
    return OutVacancyParse(is_vacancy=True, skills=list(skills))


def _kept(parsed: OutVacancyParse) -> list[str]:
    return [item.skill.value for item in parsed.skills]


class TestQuoteMustBeInTheText:
    def test_real_quote_survives(self) -> None:
        parsed = _parsed(
            SkillWithEvidence(skill=SkillType.JAVA_SCALA, evidence="сервисы на базе Spring")
        )

        drop_unsupported_skills(parsed, JAVA_VACANCY)

        assert _kept(parsed) == ["Java/Scala"]

    def test_invented_quote_is_dropped(self) -> None:
        """Ровно этот случай и наблюдался на проде."""
        parsed = _parsed(
            SkillWithEvidence(skill=SkillType.NODE_JS, evidence="разработка на Node.js")
        )

        drop_unsupported_skills(parsed, JAVA_VACANCY)

        assert _kept(parsed) == []

    def test_case_and_spacing_do_not_matter(self) -> None:
        """Модель переносит строки и меняет регистр даже когда просят копировать."""
        parsed = _parsed(
            SkillWithEvidence(skill=SkillType.JAVA_SCALA, evidence="СЕРВИСЫ   НА\nБАЗЕ Spring")
        )

        drop_unsupported_skills(parsed, JAVA_VACANCY)

        assert _kept(parsed) == ["Java/Scala"]

    def test_empty_quote_is_dropped(self) -> None:
        parsed = _parsed(SkillWithEvidence(skill=SkillType.JAVA_SCALA, evidence="  "))

        drop_unsupported_skills(parsed, JAVA_VACANCY)

        assert _kept(parsed) == []


class TestQuoteMustNameTheTechnology:
    """Цитата из текста — ещё не обоснование.

    Node.js подтверждался фрагментами «сервисы на базе Spring» и
    «backend платформы»: цитата настоящая, вывод из неё — нет.
    """

    def test_real_quote_about_another_technology_is_dropped(self) -> None:
        parsed = _parsed(
            SkillWithEvidence(skill=SkillType.NODE_JS, evidence="сервисы на базе Spring")
        )

        drop_unsupported_skills(parsed, JAVA_VACANCY)

        assert _kept(parsed) == []

    def test_umbrella_skill_is_confirmed_by_its_tools(self) -> None:
        """У DevOps нет собственного имени в тексте — его подтверждают инструменты."""
        parsed = _parsed(SkillWithEvidence(skill=SkillType.DEVOPS, evidence="GitLab CI"))

        drop_unsupported_skills(parsed, JAVA_VACANCY)

        assert _kept(parsed) == ["DevOps"]


class TestReturnValue:
    def test_counts_dropped(self) -> None:
        parsed = _parsed(
            SkillWithEvidence(skill=SkillType.JAVA_SCALA, evidence="сервисы на базе Spring"),
            SkillWithEvidence(skill=SkillType.NODE_JS, evidence="выдумка"),
            SkillWithEvidence(skill=SkillType.PYTHON, evidence="тоже выдумка"),
        )

        assert drop_unsupported_skills(parsed, JAVA_VACANCY) == 2
        assert _kept(parsed) == ["Java/Scala"]


class TestShortNamesSurvive:
    """«Go» и «C#» короче любого разумного минимума длины.

    Первая версия проверки резала их вместе с мусором, и вакансия
    `Team Lead (C#)` со стеком `C#, .NET` осталась вовсе без навыков.
    """

    def test_two_letter_name_is_enough(self) -> None:
        parsed = _parsed(SkillWithEvidence(skill=SkillType.GO, evidence="Go"))

        drop_unsupported_skills(parsed, "Разработчик DBaaS. Стек: Go, PostgreSQL, Kubernetes.")

        assert _kept(parsed) == ["Go"]

    def test_sharp_name_is_enough(self) -> None:
        parsed = _parsed(SkillWithEvidence(skill=SkillType.C_SHARP, evidence="C#"))

        drop_unsupported_skills(parsed, "Team Lead (C#). Стек: C#, .NET, Microservices.")

        assert _kept(parsed) == ["C#"]

    def test_short_junk_still_dropped_for_umbrella_skills(self) -> None:
        """У зонтичного навыка имени в тексте нет, и длина — единственная защита."""
        parsed = _parsed(SkillWithEvidence(skill=SkillType.DEVOPS, evidence="и"))

        drop_unsupported_skills(parsed, "Разработчик и инженер, GitLab CI")

        assert _kept(parsed) == []
