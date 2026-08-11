from app.application.ports.unit_of_work import DeveloperUserUnitOfWork
from app.domain.user.entities import User
from app.domain.user.value_objects import UserId


class DeveloperUserService:
    """Development-only operations for recreating Telegram user journeys."""

    def __init__(self, uow: DeveloperUserUnitOfWork) -> None:
        self._uow = uow

    async def reset_profile(self, tg_id: int) -> bool:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id_for_update(UserId(tg_id))
            if user is None:
                return False

            pristine_user = User.create(
                tg_id=tg_id,
                username=user.username,
                cv_work_formats_raw=[],
            )
            await self._uow.users.update(pristine_user)
            return True

    async def delete_user(self, tg_id: int) -> bool:
        async with self._uow:
            user_id = UserId(tg_id)
            user = await self._uow.users.get_by_tg_id_for_update(user_id)
            if user is None:
                return False

            await self._uow.developer_user_data.delete_local_user_data(user_id)
            return True


__all__ = ["DeveloperUserService"]
