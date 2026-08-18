import asyncio
from io import BytesIO
from uuid import UUID, uuid4

from app.application.dto import OutResumeParse
from app.application.ports.unit_of_work import UserUnitOfWork
from app.application.services.resume_prefill import build_prefill_draft
from app.application.services.resume_quota_service import (
    DAILY_QUOTA,
    QuotaRejection,
    ResumeQuotaService,
)
from app.core.logger import get_app_logger
from app.core.privacy import user_ref
from app.domain.user.onboarding import OnboardingDraft
from app.domain.user.resume_import import ResumeImportJob, ResumeImportStatus
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

MAX_RESUME_BYTES = 10 * 1024 * 1024

BUSY_MESSAGE = "Сейчас разбираем другие резюме. Попробуйте через пару минут."
NOT_A_RESUME_MESSAGE = "Файл не похож на резюме."
TOO_MANY_PAGES_MESSAGE = "В резюме больше 10 страниц. Нужен более компактный PDF."
PARSER_ERROR_MESSAGE = "Не удалось разобрать файл."
LLM_UNAVAILABLE_MESSAGE = "Модель временно перегружена. Попробуйте ещё раз чуть позже."
UNKNOWN_ERROR_MESSAGE = "Во время разбора резюме произошла ошибка."


class ResumeImportError(Exception):
    """Разбор не начался: причина видна пользователю до создания задачи."""


class UnsupportedResumeFormatError(ResumeImportError):
    pass


class ResumeQuotaExceededError(ResumeImportError):
    def __init__(self, rejection: QuotaRejection, retry_after_seconds: int) -> None:
        self.rejection = rejection
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Слишком часто, следующее резюме через {retry_after_seconds} с."
            if rejection is QuotaRejection.COOLDOWN
            else f"На сегодня лимит исчерпан: {DAILY_QUOTA} резюме в сутки."
        )


# Ссылки на фоновые задачи: без них сборщик мусора вправе убить задачу
# на середине разбора, и статус навсегда останется processing.
_background_tasks: set[asyncio.Task[None]] = set()


class ResumeImportService:
    def __init__(self, uow: UserUnitOfWork) -> None:
        self._uow = uow

    async def start(self, tg_id: int, file_name: str, content: bytes) -> UUID:
        try:
            parser = ParserFactory.get_parser_by_extension(file_name)
        except ValueError as exc:
            raise UnsupportedResumeFormatError("Для этого шага подходит только PDF.") from exc

        quota = ResumeQuotaService(self._uow)
        decision = await quota.check(tg_id)
        if not decision.allowed:
            assert decision.rejection is not None
            raise ResumeQuotaExceededError(decision.rejection, decision.retry_after_seconds)
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

    async def get(self, tg_id: int, job_id: UUID) -> ResumeImportJob | None:
        async with self._uow:
            return await self._uow.resume_import_jobs.get(job_id, tg_id)

    async def _process(
        self, job_id: UUID, tg_id: int, parser: BaseResumeParser, content: bytes
    ) -> None:
        try:
            await self._set_status(job_id, ResumeImportStatus.PROCESSING)
            async with acquire_parse_slot() as granted:
                if not granted:
                    await self._fail(job_id, BUSY_MESSAGE)
                    return
                buffer = BytesIO(content)
                try:
                    dto = await parser.extract_text(buffer)
                finally:
                    buffer.close()

            await self._apply(tg_id, dto)
            await self._set_status(job_id, ResumeImportStatus.COMPLETED)
        except NotAResumeError:
            await self._fail(job_id, NOT_A_RESUME_MESSAGE)
        except TooManyPagesError:
            await self._fail(job_id, TOO_MANY_PAGES_MESSAGE)
        except ParserError:
            await self._fail(job_id, PARSER_ERROR_MESSAGE)
        except TemporaryLLMUnavailableError:
            await self._fail(job_id, LLM_UNAVAILABLE_MESSAGE)
        except Exception:
            logger.exception("Resume import failed unexpectedly (user=%s)", user_ref(tg_id))
            await self._fail(job_id, UNKNOWN_ERROR_MESSAGE)

    async def _apply(self, tg_id: int, dto: OutResumeParse) -> None:
        async with self._uow:
            user = await self._uow.users.get_by_tg_id(UserId(tg_id))
            if user is None:
                raise ResumeImportError("Пользователь не найден.")
            current = user.onboarding_draft or OnboardingDraft()
            user.onboarding_draft = build_prefill_draft(dto, current)
            await self._uow.users.update(user)

    async def _set_status(self, job_id: UUID, status: ResumeImportStatus) -> None:
        async with self._uow:
            await self._uow.resume_import_jobs.set_status(job_id, status)

    async def _fail(self, job_id: UUID, message: str) -> None:
        async with self._uow:
            await self._uow.resume_import_jobs.set_status(
                job_id, ResumeImportStatus.FAILED, message
            )
