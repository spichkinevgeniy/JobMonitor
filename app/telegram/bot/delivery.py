from app.application.services.user_service import UserService
from app.core.logger import get_app_logger
from app.core.privacy import user_ref

logger = get_app_logger(__name__)


async def deactivate_user(users: UserService, tg_id: int) -> None:
    """Отключает того, кто заблокировал бота: слать ему дальше бессмысленно.

    Не падает: из-за одного пользователя рассылка останавливаться не должна.
    """
    try:
        await users.deactivate(tg_id)
    except Exception:
        logger.exception("Failed to deactivate user %s after forbidden error", user_ref(tg_id))
