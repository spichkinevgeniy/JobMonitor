from app.core.logger import get_app_logger
from app.core.privacy import user_ref
from app.domain.user.value_objects import UserId
from app.infrastructure.db import UserUnitOfWork, async_session_factory

logger = get_app_logger(__name__)


async def deactivate_user(tg_id: int) -> None:
    """Отключает того, кто заблокировал бота: слать ему дальше бессмысленно."""
    try:
        async with UserUnitOfWork(async_session_factory) as uow:
            user = await uow.users.get_by_tg_id(UserId(tg_id))
            if user is not None and user.is_active:
                user.is_active = False
                await uow.users.update(user)
    except Exception:
        logger.exception("Failed to deactivate user %s after forbidden error", user_ref(tg_id))
