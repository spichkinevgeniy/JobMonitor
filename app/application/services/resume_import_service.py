import asyncio
from io import BytesIO
from uuid import UUID, uuid4

from app.application.dto import OutResumeParse
from app.application.ports.resume_import import (
    ResumeImportJob,
    ResumeImportStatus,
)
from app.application.ports.unit_of_work import ResumeImportUnitOfWork
from app.application.services import resume_policy
from app.application.services.resume_prefill import build_prefill_draft
from app.application.services.resume_quota_service import (
    DAILY_QUOTA,
    QuotaRejection,
    ResumeQuotaService,
)
from app.core.logger import get_app_logger
from app.core.privacy import user_ref
from app.domain.user.onboarding import OnboardingDraft
from app.domain.user.value_objects import UserId
from app.infrastructure.llm_runtime import TemporaryLLMUnavailableError
from app.infrastructure.parsers import (
    NotAResumeError,
    ParserError,
    ParserFactory,
    TooManyPagesError,
)
from app.infrastructure.parsers.base import BaseResumeParser
from app.infrastructure.parsers.concurrency import acquire_parse_slot

logger = get_app_logger(__name__)


class ResumeImportError(Exception):
    """Разбор не начался: причина видна пользователю до создания задачи."""


class UnsupportedResumeFormatError(ResumeImportError):
    pass


class ResumeQuotaExceededError(ResumeImportError):
    def __init__(self, rejection: QuotaRejection, retry_after_seconds: int) -> None:
        self.rejection = rejection
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            resume_policy.cooldown_text(retry_after_seconds)
            if rejection is QuotaRejection.COOLDOWN
            else resume_policy.daily_quota_text(DAILY_QUOTA)
        )


# Ссылки на фоновые задачи: без них сборщик мусора вправе убить задачу
# на середине разбора, и статус навсегда останется processing.
_background_tasks: set[asyncio.Task[None]] = set()


class ResumeImportService:
    def __init__(self, uow: ResumeImportUnitOfWork) -> None:
        self._uow = uow

    async def start(self, tg_id: int, file_name: str, content: bytes) -> UUID:
        try:
            parser = ParserFactory.get_parser_by_extension(file_name)
        except ValueError as exc:
            raise UnsupportedResumeFormatError(resume_policy.UNSUPPORTED_FORMAT) from exc

        quota = ResumeQuotaService(self._uow)
        decision = await quota.check(tg_id)
        if not decision.allowed:
            assert decision.rejection is not None
            raise ResumeQuotaExceededError(decision.rejection, decision.retry_after_seconds)
        # Списываем до постановки в очередь, а не внутри слота как в боте:
        # у HTTP нет пошаговости, и иначе десятки запросов пройдут проверку
        # раньше, чем первый успеет отметиться.
        await quota.register(tg_id)

        job = ResumeImportJob(
            id=uuid4(),
            user_tg_id=tg_id,
            status=ResumeImportStatus.QUEUED,
        )
        async with self._uow:
            await self._uow.resume_import_jobs.add(job)

        # Файл передаётся задаче в памяти и на диск не попадает.
        task = asyncio.create_task(self._process(job.id, tg_id, parser, content))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return job.id

    async def fail_orphaned(self) -> int:
        async with self._uow:
            return await self._uow.resume_import_jobs.fail_unfinished(resume_policy.INTERRUPTED)

    async def get(self, tg_id: int, job_id: UUID) -> ResumeImportJob | None:
        async with self._uow:
            return await self._uow.resume_import_jobs.get(job_id, tg_id)

    async def _process(
        self, job_id: UUID, tg_id: int, parser: BaseResumeParser, content: bytes
    ) -> None:
        try:
            async with acquire_parse_slot() as granted:
                if not granted:
                    await self._set_status(job_id, ResumeImportStatus.FAILED, resume_policy.BUSY)
                    return
                # До этого места задача честно стоит в очереди, а не «в работе».
                await self._set_status(job_id, ResumeImportStatus.PROCESSING)
                buffer = BytesIO(content)
                try:
                    dto = await parser.extract_text(buffer)
                finally:
                    buffer.close()

            await self._apply(tg_id, dto)
            await self._set_status(job_id, ResumeImportStatus.COMPLETED)
        except NotAResumeError:
            await self._set_status(job_id, ResumeImportStatus.FAILED, resume_policy.NOT_A_RESUME)
        except TooManyPagesError:
            await self._set_status(job_id, ResumeImportStatus.FAILED, resume_policy.TOO_MANY_PAGES)
        except ParserError:
            await self._set_status(job_id, ResumeImportStatus.FAILED, resume_policy.PARSER_ERROR)
        except TemporaryLLMUnavailableError:
            await self._set_status(job_id, ResumeImportStatus.FAILED, resume_policy.LLM_UNAVAILABLE)
        except Exception:
            logger.exception("Resume import failed unexpectedly (user=%s)", user_ref(tg_id))
            await self._set_status(job_id, ResumeImportStatus.FAILED, resume_policy.UNKNOWN_ERROR)

    async def _apply(self, tg_id: int, dto: OutResumeParse) -> None:
        async with self._uow:
            # Разбор длится десятки секунд: без блокировки правка черновика,
            # прилетевшая за это время, была бы молча затёрта.
            user = await self._uow.users.get_by_tg_id_for_update(UserId(tg_id))
            if user is None:
                raise LookupError(f"user {user_ref(tg_id)} disappeared during import")
            current = user.onboarding_draft or OnboardingDraft()
            user.onboarding_draft = build_prefill_draft(dto, current)
            await self._uow.users.update(user)

    async def _set_status(
        self, job_id: UUID, status: ResumeImportStatus, error: str | None = None
    ) -> None:
        async with self._uow:
            await self._uow.resume_import_jobs.set_status(job_id, status, error)
