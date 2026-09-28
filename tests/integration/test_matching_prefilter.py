"""Предфильтр подбора: операторы JSONB, которые на фейках не проверить.

По нему решается, кому вообще смотреть вакансию. Ошибка здесь молча
оставляет людей без вакансий, а юнит-тесты её не заметят: там нет базы.
"""

from app.domain.user.entities import User
from app.infrastructure.db import UserUnitOfWork, async_session_factory


async def add_users(*users: User) -> None:
    uow = UserUnitOfWork(async_session_factory)
    async with uow:
        for user in users:
            await uow.users.add(user)


async def candidates(specializations: set[str], skills: set[str]) -> set[int]:
    uow = UserUnitOfWork(async_session_factory)
    async with uow:
        found = await uow.users.find_prefiltered_candidates(
            specializations=specializations, skills=skills, is_active=True
        )
    return {user.tg_id.value for user in found}


async def test_needs_both_a_shared_specialization_and_a_shared_skill() -> None:
    await add_users(
        User.create(tg_id=1, cv_specializations_raw=["Backend"], cv_skills_raw=["Python"]),
        User.create(tg_id=2, cv_specializations_raw=["Frontend"], cv_skills_raw=["Python"]),
        User.create(tg_id=3, cv_specializations_raw=["Backend"], cv_skills_raw=["Go"]),
        User.create(
            tg_id=4,
            cv_specializations_raw=["Backend", "Analytics"],
            cv_skills_raw=["SQL", "Python"],
        ),
    )

    assert await candidates({"Backend"}, {"Python", "Kafka"}) == {1, 4}


async def test_inactive_users_are_left_out() -> None:
    await add_users(
        User.create(tg_id=1, cv_specializations_raw=["Backend"], cv_skills_raw=["Python"]),
        User.create(
            tg_id=2,
            cv_specializations_raw=["Backend"],
            cv_skills_raw=["Python"],
            is_active=False,
        ),
    )

    assert await candidates({"Backend"}, {"Python"}) == {1}


async def test_values_with_spaces_and_symbols_match_exactly() -> None:
    """Названия вроде «C#» и «Data Science / ML» должны сравниваться как есть."""
    await add_users(
        User.create(tg_id=1, cv_specializations_raw=["Data Science / ML"], cv_skills_raw=["C#"]),
        User.create(tg_id=2, cv_specializations_raw=["Backend"], cv_skills_raw=["C++"]),
    )

    assert await candidates({"Data Science / ML"}, {"C#"}) == {1}
