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


@runtime_checkable
class IDocumentSender(Protocol):
    async def send_document(
        self,
        user_tg_id: int,
        filename: str,
        content: bytes,
        caption: str,
    ) -> None: ...
