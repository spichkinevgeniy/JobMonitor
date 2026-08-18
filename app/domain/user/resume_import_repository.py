from typing import Protocol
from uuid import UUID

from app.domain.user.resume_import import ResumeImportJob, ResumeImportStatus


class IResumeImportJobRepository(Protocol):
    async def add(self, job: ResumeImportJob) -> None: ...

    async def get(self, job_id: UUID, user_tg_id: int) -> ResumeImportJob | None: ...

    async def set_status(
        self,
        job_id: UUID,
        status: ResumeImportStatus,
        error: str | None = None,
    ) -> None: ...
