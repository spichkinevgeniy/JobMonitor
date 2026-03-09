from app.application.dto import OutResumeParse
from app.application.ports.unit_of_work import UserUnitOfWork
from app.domain.shared.value_objects import (
    PrimaryLanguages,
    Specializations,
    TechStack,
    WorkFormat,
)
from app.domain.user.entities import User
from app.domain.user.value_objects import (
    FilterMode,
    UserId,
)


class UserService:
    def __init__(self, uow: UserUnitOfWork) -> None:
        self._uow = uow

    async def get_user_by_tg_id(self, tg_id: int) -> User | None:
        async with self._uow:
            return await self._uow.users.get_by_tg_id(UserId(tg_id))

    async def get_or_create_user(self, tg_id: int, username: str | None) -> User:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                user = User.create(tg_id=tg_id, username=username)
                await self._uow.users.add(user)
                return user

            if user.username != username:
                user.username = username
                await self._uow.users.update(user)
            return user

    async def update_filters(
        self,
        tg_id: int,
        experience_min_months: int | None,
        salary_mode: FilterMode,
        work_format: WorkFormat | None,
        work_format_mode: FilterMode,
    ) -> bool:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                return False
            user.filter_experience_min_months = experience_min_months
            user.filter_salary_mode = salary_mode
            user.cv_work_format = work_format
            user.filter_work_format_mode = work_format_mode
            await self._uow.users.update(user)
        return True

    async def update_resume(self, tg_id: int, dto: OutResumeParse) -> bool:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                return False

            user.cv_text = dto.full_relevant_text_from_resume
            user.cv_specializations = Specializations.from_strs(
                [item.value for item in dto.specializations]
            )
            user.cv_primary_languages = PrimaryLanguages.from_strs(
                [item.value for item in dto.primary_languages]
            )

            tech_stack = TechStack.create(dto.tech_stack)
            user.cv_tech_stack = tech_stack if tech_stack.items else None

            user.cv_experience_months = max(0, dto.experience_months)
            user.cv_salary = dto.salary

            work_format = dto.work_format
            user.cv_work_format = None if work_format == WorkFormat.UNDEFINED else work_format

            await self._uow.users.update(user)
        return True
