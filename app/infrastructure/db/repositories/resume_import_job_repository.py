from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.resume_import import (
    IResumeImportJobRepository,
    ResumeImportJob,
    ResumeImportStatus,
)
from app.infrastructure.db.models import ResumeImportJob as ResumeImportJobModel


class ResumeImportJobRepository(IResumeImportJobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, job: ResumeImportJob) -> None:
        self._session.add(
            ResumeImportJobModel(
                id=job.id,
                user_tg_id=job.user_tg_id,
                status=job.status.value,
                error=job.error,
            )
        )
        await self._session.flush()

    async def get(self, job_id: UUID, user_tg_id: int) -> ResumeImportJob | None:
        """Владелец в условии, а не в проверке после выборки.

        Иначе по чужому job_id видно, чем закончился чужой разбор.
        """
        result = await self._session.execute(
            select(ResumeImportJobModel)
            .where(ResumeImportJobModel.id == job_id)
            .where(ResumeImportJobModel.user_tg_id == user_tg_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return ResumeImportJob(
            id=model.id,
            user_tg_id=model.user_tg_id,
            status=ResumeImportStatus(model.status),
            error=model.error,
        )

    async def set_status(
        self,
        job_id: UUID,
        status: ResumeImportStatus,
        error: str | None = None,
    ) -> None:
        await self._session.execute(
            update(ResumeImportJobModel)
            .where(ResumeImportJobModel.id == job_id)
            .values(status=status.value, error=error)
        )
        await self._session.flush()

    async def fail_unfinished(self, error: str) -> int:
        """Задачи, оставшиеся в работе с прошлого запуска.

        Выполнять их некому: фоновые задачи живут в процессе и умирают
        вместе с ним, а строка в базе переживает перезапуск.
        """
        result = await self._session.execute(
            update(ResumeImportJobModel)
            .where(
                ResumeImportJobModel.status.in_(
                    (ResumeImportStatus.QUEUED.value, ResumeImportStatus.PROCESSING.value)
                )
            )
            .values(status=ResumeImportStatus.FAILED.value, error=error)
        )
        await self._session.flush()
        return result.rowcount or 0
