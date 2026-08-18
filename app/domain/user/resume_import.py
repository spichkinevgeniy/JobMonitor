from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ResumeImportStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class ResumeImportJob:
    """Состояние разбора резюме. Сам файл здесь не хранится и нигде не оседает."""

    id: UUID
    user_tg_id: int
    status: ResumeImportStatus
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_finished(self) -> bool:
        return self.status in (ResumeImportStatus.COMPLETED, ResumeImportStatus.FAILED)
