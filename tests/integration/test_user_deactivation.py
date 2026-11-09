"""Дата блокировки на настоящем Postgres: запись, чтение и заполнение старых строк."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from app.application.services.user_service import UserService
from app.domain.user.entities import User
from app.domain.user.value_objects import UserId
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.infrastructure.db.models import User as UserModel
from app.infrastructure.db.models import VacancyDispatchLog
from tests.integration.conftest import alembic


async def _add_user(tg_id: int, is_active: bool = True) -> None:
    async with UserUnitOfWork(async_session_factory) as uow:
        await uow.users.add(User.create(tg_id=tg_id, is_active=is_active))


async def _add_dispatch(tg_id: int, at: datetime) -> None:
    async with async_session_factory() as session:
        session.add(VacancyDispatchLog(user_tg_id=tg_id, vacancy_id=uuid4(), dispatched_at=at))
        await session.commit()


async def _stored_date(tg_id: int) -> datetime | None:
    async with async_session_factory() as session:
        query = select(UserModel.deactivated_at).where(UserModel.tg_id == tg_id)
        return (await session.execute(query)).scalar_one()


async def test_deactivation_date_is_saved_and_read_back() -> None:
    await _add_user(1)

    await UserService(UserUnitOfWork(async_session_factory)).deactivate(1)

    stored = await _stored_date(1)
    assert stored is not None
    assert datetime.now(UTC) - stored < timedelta(minutes=1)
    async with UserUnitOfWork(async_session_factory) as uow:
        user = await uow.users.get_by_tg_id(UserId(1))
    assert user is not None
    assert user.is_active is False
    assert user.deactivated_at == stored


async def test_migration_fills_date_only_for_those_who_already_left() -> None:
    """Последняя доставка у ушедших; без доставок и у активных даты быть не должно."""
    first = datetime(2026, 10, 1, 12, tzinfo=UTC)
    last = datetime(2026, 10, 5, 12, tzinfo=UTC)
    await _add_user(1, is_active=False)
    await _add_dispatch(1, first)
    await _add_dispatch(1, last)
    await _add_user(2, is_active=False)
    await _add_user(3, is_active=True)
    await _add_dispatch(3, last)

    alembic("downgrade", "-1")
    alembic("upgrade", "head")

    assert await _stored_date(1) == last
    assert await _stored_date(2) is None
    assert await _stored_date(3) is None
