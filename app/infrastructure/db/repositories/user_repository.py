from datetime import date, datetime
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select, update
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.entities import User
from app.domain.user.repository import IUserRepository
from app.domain.user.value_objects import UserId
from app.infrastructure.db.mappers.user import apply_user, user_from_model, user_to_model
from app.infrastructure.db.models import ResumeUploadLog as ResumeUploadLogModel
from app.infrastructure.db.models import User as UserModel
from app.infrastructure.db.models import VacancyDispatchLog as VacancyDispatchLogModel
from app.infrastructure.db.models import WeeklyPulseLog as WeeklyPulseLogModel


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

    async def list_active_tg_ids(self) -> list[int]:
        result = await self._session.execute(
            select(UserModel.tg_id).where(UserModel.is_active.is_(True))
        )
        return [row[0] for row in result.all()]

    async def list_pulse_recipients(self) -> list[User]:
        result = await self._session.execute(
            select(UserModel).where(
                UserModel.is_active.is_(True), UserModel.pulse_enabled.is_(True)
            )
        )
        return [user_from_model(model) for model in result.scalars().all()]

    async def claim_weekly_pulse(self, tg_id: int, week_start: date) -> bool:
        """Занимает неделю за пользователем до отправки.

        Строку пишем до отправки, а не после: при рестарте посреди рассылки
        кто-то останется без сводки, но никто не получит её дважды.
        """
        result = await self._session.execute(
            pg_insert(WeeklyPulseLogModel)
            .values(user_tg_id=tg_id, week_start=week_start, status="pending")
            .on_conflict_do_nothing()
            .returning(WeeklyPulseLogModel.user_tg_id)
        )
        return result.scalar_one_or_none() is not None

    async def set_weekly_pulse_status(self, tg_id: int, week_start: date, status: str) -> None:
        await self._session.execute(
            update(WeeklyPulseLogModel)
            .where(
                WeeklyPulseLogModel.user_tg_id == tg_id,
                WeeklyPulseLogModel.week_start == week_start,
            )
            .values(status=status)
        )

    async def get_resume_upload_stats(
        self, tg_id: int, since: datetime
    ) -> tuple[int, datetime | None]:
        """Число загрузок в окне и время последней — она может быть старше окна."""
        result = await self._session.execute(
            select(
                func.count().filter(ResumeUploadLogModel.uploaded_at >= since),
                func.max(ResumeUploadLogModel.uploaded_at),
            ).where(ResumeUploadLogModel.user_tg_id == tg_id)
        )
        count, last_uploaded_at = result.one()
        return count or 0, last_uploaded_at

    async def log_resume_upload(self, tg_id: int) -> None:
        self._session.add(ResumeUploadLogModel(user_tg_id=tg_id))
        await self._session.flush()

    async def delete_by_tg_id(self, tg_id: UserId) -> bool:
        """Профиль и все его журналы. Внешних ключей нет, каскад не сработает."""
        for model in (VacancyDispatchLogModel, ResumeUploadLogModel, WeeklyPulseLogModel):
            await self._session.execute(delete(model).where(model.user_tg_id == tg_id.value))
        # execute() объявлен как Result, но на DML возвращает CursorResult —
        # только у него есть rowcount. Приведение вместо ignore, чтобы не
        # глушить настоящие ошибки в этой строке.
        result = cast(
            "CursorResult[Any]",
            await self._session.execute(delete(UserModel).where(UserModel.tg_id == tg_id.value)),
        )
        await self._session.flush()
        return bool(result.rowcount)
