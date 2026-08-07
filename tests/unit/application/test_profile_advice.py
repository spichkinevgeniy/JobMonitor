"""Потеря на префильтре и подсказки, какие навыки её сокращают.

Воронка начинается после префильтра по навыкам, поэтому раньше человек с
одним навыком видел «отсеяно ноль» и делал вывод, что вакансий нет.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.application.services.stats_service import (
    MIN_SUGGESTION_UNLOCKS,
    StatsService,
)
from app.domain.shared.value_objects import Grade, WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import LevelFilterMode
from app.domain.vacancy.entities import Vacancy

NOW = datetime.now(UTC)


def _vacancy(skills: list[str], grade: Grade = Grade.UNDEFINED) -> Vacancy:
    return Vacancy.create(
        vacancy_id=uuid4(),
        text="Вакансия",
        specializations_raw=["Backend"],
        skills_raw=skills,
        mirror_chat_id=1,
        mirror_message_id=1,
        work_format=WorkFormat.REMOTE,
        grade=grade,
        created_at=NOW - timedelta(days=1),
    )


def _user(skills: list[str], **kwargs: object) -> User:
    return User.create(
        tg_id=1,
        cv_specializations_raw=["Backend"],
        cv_skills_raw=skills,
        **kwargs,  # type: ignore[arg-type]
    )


class _Repo:
    def __init__(self, vacancies: list[Vacancy]) -> None:
        self._v = vacancies

    async def find_for_profile_since(
        self, specializations: set[str], skills: set[str], since: datetime
    ) -> list[Vacancy]:
        if not specializations or not skills:
            return []
        return [
            v
            for v in self._v
            if {i.value for i in v.specializations.items} & specializations
            and {i.value for i in v.skills.items} & skills
        ]

    async def find_for_specializations_since(
        self, specializations: set[str], since: datetime
    ) -> list[Vacancy]:
        return [v for v in self._v if {i.value for i in v.specializations.items} & specializations]


class _Uow:
    def __init__(self, vacancies: list[Vacancy]) -> None:
        self.vacancies = _Repo(vacancies)

    async def __aenter__(self) -> "_Uow":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


async def _stats(vacancies: list[Vacancy], user: User):  # type: ignore[no-untyped-def]
    return await StatsService(_Uow(vacancies)).build_profile_stats(user)  # type: ignore[arg-type]


class TestFunnelSeesPrefilterLoss:
    async def test_counts_vacancies_lost_on_skills(self) -> None:
        vacancies = [_vacancy(["Python"])] + [_vacancy(["Go"]) for _ in range(4)]

        funnel = (await _stats(vacancies, _user(["Python"]))).funnel

        assert funnel.specialization_total == 5
        assert funnel.skills_mismatch == 4
        assert funnel.matched == 1

    async def test_nothing_lost_when_all_skills_match(self) -> None:
        vacancies = [_vacancy(["Python"]) for _ in range(3)]

        funnel = (await _stats(vacancies, _user(["Python"]))).funnel

        assert funnel.skills_mismatch == 0
        assert funnel.specialization_total == funnel.matched

    async def test_total_is_larger_than_prefiltered(self) -> None:
        """Именно это расхождение раньше не показывалось."""
        vacancies = [_vacancy(["Python"])] + [_vacancy(["Rust"]) for _ in range(9)]

        funnel = (await _stats(vacancies, _user(["Python"]))).funnel

        assert funnel.specialization_total == 10
        assert funnel.total == 1


class TestSkillSuggestions:
    async def test_suggests_the_skill_that_unlocks_most(self) -> None:
        vacancies = [_vacancy(["Python"])] + [_vacancy(["Go"]) for _ in range(5)]

        suggestions = (await _stats(vacancies, _user(["Python"]))).skill_suggestions

        assert suggestions[0].skill == "Go"
        assert suggestions[0].unlocks == 5

    async def test_ignores_skills_below_threshold(self) -> None:
        """Иначе в хвост лезут случайные совпадения."""
        vacancies = [_vacancy(["Python"])] + [
            _vacancy(["Rust"]) for _ in range(MIN_SUGGESTION_UNLOCKS - 1)
        ]

        suggestions = (await _stats(vacancies, _user(["Python"]))).skill_suggestions

        assert suggestions == []

    async def test_never_suggests_what_user_already_has(self) -> None:
        vacancies = [_vacancy(["Python", "Go"]) for _ in range(5)]

        suggestions = (await _stats(vacancies, _user(["Python"]))).skill_suggestions

        assert all(item.skill != "Python" for item in suggestions)

    async def test_counts_only_vacancies_that_would_actually_arrive(self) -> None:
        """Мало добавить навык — вакансия должна пройти и остальные фильтры."""
        vacancies = [_vacancy(["Go"], grade=Grade.LEAD) for _ in range(5)]
        user = _user(["Python"], cv_grade=Grade.JUNIOR, filter_grade_mode=LevelFilterMode.UP_TO)

        suggestions = (await _stats(vacancies, user)).skill_suggestions

        assert suggestions == []

    async def test_profile_without_skills_gets_suggestions(self) -> None:
        """Ему они нужнее всех: без навыков префильтр не пропускает ничего."""
        vacancies = [_vacancy(["Go"]) for _ in range(5)]

        suggestions = (await _stats(vacancies, _user([]))).skill_suggestions

        assert suggestions[0].skill == "Go"

    async def test_profile_without_specialization_gets_nothing(self) -> None:
        vacancies = [_vacancy(["Go"]) for _ in range(5)]
        user = User.create(tg_id=1, cv_specializations_raw=[], cv_skills_raw=[])

        assert (await _stats(vacancies, user)).skill_suggestions == []
