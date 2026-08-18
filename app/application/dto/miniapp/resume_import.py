from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.user.resume_import import ResumeImportStatus


class ResumeImportJobCreated(BaseModel):
    job_id: UUID
    status: ResumeImportStatus = Field(default=ResumeImportStatus.QUEUED)


class ResumeImportJobState(BaseModel):
    job_id: UUID
    status: ResumeImportStatus
    error: str | None = None
