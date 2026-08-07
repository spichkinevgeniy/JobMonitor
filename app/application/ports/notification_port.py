from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DispatchTarget:
    """Получатель и то, из-за чего вакансия ему подошла.

    Совпадение считаем в момент отправки: профиль потом изменится, и
    пересчёт задним числом покажет неправду.
    """

    user_id: int
    matched_skills: list[str] = field(default_factory=list)


@runtime_checkable
class INotificationService(Protocol):
    async def dispatch_vacancy(
        self,
        vacancy_id: UUID,
        mirror_chat_id: int,
        mirror_message_id: int,
        targets: list[DispatchTarget],
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
