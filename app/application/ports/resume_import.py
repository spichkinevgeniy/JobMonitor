from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class ResumeImportStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class ResumeImportJob:
    """Состояние разбора резюме: нужно только затем, чтобы мини-апп мог
    опросить результат. Сам файл здесь не хранится и нигде не оседает."""

    id: UUID
    user_tg_id: int
    status: ResumeImportStatus
    error: str | None = None


class IResumeImportJobRepository(Protocol):
    async def add(self, job: ResumeImportJob) -> None: ...

    async def get(self, job_id: UUID, user_tg_id: int) -> ResumeImportJob | None: ...

    async def set_status(
        self,
        job_id: UUID,
        status: ResumeImportStatus,
        error: str | None = None,
    ) -> None: ...
