from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.application.dto.miniapp import ResumeImportJobCreated, ResumeImportJobState
from app.application.ports.observability_port import Feature
from app.application.services.resume_import_service import (
    ResumeImportService,
    ResumeQuotaExceededError,
    UnsupportedResumeFormatError,
)
from app.application.services.resume_policy import MAX_RESUME_BYTES
from app.domain.user.entities import User
from app.infrastructure.observability import observe_feature
from app.telegram.bot.views import build_resume_file_too_large_text
from app.telegram.miniapp.auth import MiniAppUserContext
from app.telegram.miniapp.deps import (
    get_current_user,
    get_resume_import_service,
    get_user_context,
)
from app.telegram.miniapp.onboarding_routes import ONBOARDING_PREFIX

router = APIRouter(prefix=ONBOARDING_PREFIX, tags=["onboarding"])


@router.post(
    "/resume-prefill",
    response_model=ResumeImportJobCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_resume_prefill(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResumeImportService, Depends(get_resume_import_service)],
    file: Annotated[UploadFile, File()],
) -> ResumeImportJobCreated:
    content = await _read_within_limit(file)

    try:
        job_id = await service.start(user.tg_id.value, file.filename or "", content)
    except UnsupportedResumeFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc
    except ResumeQuotaExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    observe_feature(Feature.RESUME_UPLOAD)
    return ResumeImportJobCreated(job_id=job_id)


@router.get("/resume-prefill/{job_id}", response_model=ResumeImportJobState)
async def get_resume_prefill_state(
    job_id: UUID,
    context: Annotated[MiniAppUserContext, Depends(get_user_context)],
    service: Annotated[ResumeImportService, Depends(get_resume_import_service)],
) -> ResumeImportJobState:
    job = await service.get(context.tg_id, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена.")
    return ResumeImportJobState(job_id=job.id, status=job.status, error=job.error)


async def _read_within_limit(file: UploadFile) -> bytes:
    """Отсекает файл по размеру, уже известному после разбора формы.

    Раньше здесь был чтение по кускам «чтобы файл не осел на диске» — это
    было неправдой: Starlette разбирает и спулит тело до входа в хендлер.
    От по-настоящему больших тел защищает client_max_body_size в nginx.
    """
    if (file.size or 0) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=build_resume_file_too_large_text(),
        )
    return await file.read()
