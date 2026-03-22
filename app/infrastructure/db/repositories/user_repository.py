from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.entities import User
from app.domain.user.repository import IUserRepository
from app.domain.user.value_objects import UserId
from app.infrastructure.db.mappers.user import apply_user, user_from_model, user_to_model
from app.infrastructure.db.models import User as UserModel


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_tg_id(self, tg_id: UserId) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.tg_id == tg_id.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return user_from_model(model)

    async def add(self, user: User) -> None:
        self._session.add(user_to_model(user))

    async def update(self, user: User) -> None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.tg_id == user.tg_id.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("User not found")
        apply_user(model, user)

    async def upsert(self, user: User) -> None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.tg_id == user.tg_id.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            self._session.add(user_to_model(user))
            return
        apply_user(model, user)

    async def count_total(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(UserModel))
        return int(result.scalar_one())

    async def count_active(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(UserModel).where(UserModel.is_active.is_(True))
        )
        return int(result.scalar_one())

    async def find_prefiltered_candidates(
        self,
        specializations: set[str],
        skills: set[str],
        is_active: bool = True,
    ) -> list[User]:
        query = select(UserModel)
        query = query.where(UserModel.is_active.is_(is_active))

        if specializations:
            query = query.where(
                UserModel.cv_specializations.bool_op("?|")(array(sorted(specializations)))
            )
        if skills:
            query = query.where(UserModel.cv_skills.bool_op("?|")(array(sorted(skills))))

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [user_from_model(model) for model in models]
