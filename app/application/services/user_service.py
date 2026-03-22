from app.application.dto import OutResumeParse
from app.application.ports.unit_of_work import UserUnitOfWork
from app.domain.shared.value_objects import (
    CurrencyType,
    ExperienceLevel,
    Grade,
    Salary,
    Skills,
    Specializations,
    WorkFormat,
)
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, LevelFilterMode, UserId


class UserService:
    def __init__(self, uow: UserUnitOfWork) -> None:
        self._uow = uow

    async def get_user_by_tg_id(self, tg_id: int) -> User | None:
        async with self._uow:
            return await self._uow.users.get_by_tg_id(UserId(tg_id))

    async def get_or_create_user(self, tg_id: int, username: str | None) -> tuple[User, bool]:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                user = User.create(tg_id=tg_id, username=username)
                await self._uow.users.add(user)
                return user, True

            if user.username != username:
                user.username = username
                await self._uow.users.update(user)
            return user, False

    async def update_resume(self, tg_id: int, dto: OutResumeParse) -> bool:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                return False

            user.cv_text = dto.full_relevant_text_from_resume
            user.cv_specializations = Specializations.from_strs(
                [item.value for item in dto.specializations]
            )
            user.cv_skills = Skills.from_strs([item.value for item in dto.skills])

            user.cv_salary = dto.salary
            if dto.salary is not None and dto.salary.amount is not None:
                user.filter_salary_mode = FilterMode.STRICT
            else:
                user.cv_salary = None
                user.filter_salary_mode = FilterMode.SOFT

            user.cv_grade = None if dto.grade == Grade.UNDEFINED else dto.grade
            user.filter_grade_mode = (
                LevelFilterMode.UP_TO if user.cv_grade is not None else LevelFilterMode.IGNORE
            )

            user.cv_experience_level = (
                None if dto.experience_level == ExperienceLevel.UNDEFINED else dto.experience_level
            )
            user.filter_experience_mode = (
                LevelFilterMode.UP_TO
                if user.cv_experience_level is not None
                else LevelFilterMode.IGNORE
            )

            work_format = dto.work_format
            user.cv_work_format = None if work_format == WorkFormat.UNDEFINED else work_format
            if user.cv_work_format is not None:
                user.filter_work_format_mode = FilterMode.STRICT
            else:
                user.filter_work_format_mode = FilterMode.SOFT

            await self._uow.users.update(user)
        return True

    async def update_profile_specializations_and_skills(
        self,
        tg_id: int,
        specializations: list[str],
        skills: list[str],
    ) -> bool:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                return False

            user.cv_specializations = Specializations.from_strs(specializations)
            user.cv_skills = Skills.from_strs(skills)
            await self._uow.users.update(user)
        return True

    async def update_profile_work_format_filter(
        self,
        tg_id: int,
        work_format: WorkFormat | None,
        work_format_mode: FilterMode,
    ) -> bool:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                return False

            normalized_work_format = None if work_format == WorkFormat.UNDEFINED else work_format
            user.cv_work_format = normalized_work_format
            user.filter_work_format_mode = (
                work_format_mode if normalized_work_format is not None else FilterMode.SOFT
            )
            await self._uow.users.update(user)
        return True

    async def update_profile_level_filters(
        self,
        tg_id: int,
        grade: Grade | None,
        grade_mode: LevelFilterMode,
        experience_level: ExperienceLevel | None,
        experience_mode: LevelFilterMode,
    ) -> bool:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                return False

            normalized_grade = None if grade == Grade.UNDEFINED else grade
            user.cv_grade = normalized_grade
            user.filter_grade_mode = (
                grade_mode if normalized_grade is not None else LevelFilterMode.IGNORE
            )

            normalized_experience = (
                None if experience_level == ExperienceLevel.UNDEFINED else experience_level
            )
            user.cv_experience_level = normalized_experience
            user.filter_experience_mode = (
                experience_mode if normalized_experience is not None else LevelFilterMode.IGNORE
            )

            await self._uow.users.update(user)
        return True

    async def update_profile_salary_filter(
        self,
        tg_id: int,
        salary_amount_rub: int | None,
        salary_mode: FilterMode,
    ) -> bool:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                return False

            if salary_mode == FilterMode.STRICT and salary_amount_rub is not None:
                user.cv_salary = Salary.create(
                    amount=salary_amount_rub,
                    currency=CurrencyType.RUB.value,
                )
                user.filter_salary_mode = FilterMode.STRICT
            else:
                user.cv_salary = None
                user.filter_salary_mode = FilterMode.SOFT

            await self._uow.users.update(user)
        return True
