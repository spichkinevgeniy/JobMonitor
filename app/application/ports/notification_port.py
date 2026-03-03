from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class INotificationService(Protocol):
    async def dispatch_vacancy(
        self,
        vacancy_id: UUID,
        mirror_chat_id: int,
        mirror_message_id: int,
        user_ids: list[int],
    ) -> None: ...
