"""Загрузка резюме из мини-аппа: доступ, лимиты, владение задачей."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.ports.resume_import import ResumeImportJob, ResumeImportStatus
from app.application.services.resume_import_service import (
    ResumeQuotaExceededError,
    UnsupportedResumeFormatError,
)
from app.application.services.resume_policy import MAX_RESUME_BYTES
from app.application.services.resume_quota_service import QuotaRejection
from app.domain.user.entities import User
from app.telegram.miniapp.app import build_miniapp_app
from app.telegram.miniapp.auth import MiniAppUserContext
from app.telegram.miniapp.deps import (
    get_current_user,
    get_resume_import_service,
    get_user_context,
)

OWNER_TG_ID = 123


class _ServiceStub:
    def __init__(self, raises: Exception | None = None) -> None:
        self.raises = raises
        self.started: list[tuple[int, str, int]] = []
        self.job_id = uuid4()

    async def start(self, tg_id: int, file_name: str, content: bytes) -> UUID:
        if self.raises is not None:
            raise self.raises
        self.started.append((tg_id, file_name, len(content)))
        return self.job_id

    async def get(self, tg_id: int, job_id: UUID) -> ResumeImportJob | None:
        if tg_id != OWNER_TG_ID or job_id != self.job_id:
            return None
        return ResumeImportJob(id=job_id, user_tg_id=tg_id, status=ResumeImportStatus.COMPLETED)


def _client(service: _ServiceStub) -> TestClient:
    app = build_miniapp_app()
    app.dependency_overrides[get_current_user] = lambda: User.create(tg_id=OWNER_TG_ID)
    app.dependency_overrides[get_user_context] = lambda: MiniAppUserContext(
        tg_id=OWNER_TG_ID, username="tester"
    )
    app.dependency_overrides[get_resume_import_service] = lambda: service
    return TestClient(app)


def _pdf(size: int = 1024) -> bytes:
    return b"%PDF-1.4\n" + b"0" * size


class TestUpload:
    def test_requires_telegram_header(self) -> None:
        app = build_miniapp_app()
        app.dependency_overrides[get_resume_import_service] = lambda: _ServiceStub()

        response = TestClient(app).post(
            "/miniapp/api/onboarding/resume-prefill",
            files={"file": ("cv.pdf", _pdf(), "application/pdf")},
        )

        assert response.status_code == 401

    def test_accepts_pdf_and_returns_job(self) -> None:
        service = _ServiceStub()

        response = _client(service).post(
            "/miniapp/api/onboarding/resume-prefill",
            files={"file": ("cv.pdf", _pdf(), "application/pdf")},
        )

        assert response.status_code == 202
        assert response.json()["status"] == "queued"
        assert service.started[0][0] == OWNER_TG_ID

    def test_rejects_file_over_limit(self) -> None:
        """Лимит должен срабатывать до того, как файл целиком осядет на диске."""
        service = _ServiceStub()

        response = _client(service).post(
            "/miniapp/api/onboarding/resume-prefill",
            files={"file": ("cv.pdf", b"0" * (MAX_RESUME_BYTES + 1), "application/pdf")},
        )

        assert response.status_code == 413
        assert service.started == []

    def test_rejects_unsupported_format(self) -> None:
        service = _ServiceStub(raises=UnsupportedResumeFormatError("Только PDF."))

        response = _client(service).post(
            "/miniapp/api/onboarding/resume-prefill",
            files={"file": ("cv.docx", b"PK\x03\x04", "application/octet-stream")},
        )

        assert response.status_code == 415

    @pytest.mark.parametrize("rejection", [QuotaRejection.COOLDOWN, QuotaRejection.DAILY_QUOTA])
    def test_quota_is_not_bypassed(self, rejection: QuotaRejection) -> None:
        """Веб-загрузка обязана считаться той же квотой, что и загрузка в боте."""
        service = _ServiceStub(raises=ResumeQuotaExceededError(rejection, 42))

        response = _client(service).post(
            "/miniapp/api/onboarding/resume-prefill",
            files={"file": ("cv.pdf", _pdf(), "application/pdf")},
        )

        assert response.status_code == 429
        assert response.headers["Retry-After"] == "42"


class TestStatus:
    def test_owner_sees_own_job(self) -> None:
        service = _ServiceStub()

        response = _client(service).get(
            f"/miniapp/api/onboarding/resume-prefill/{service.job_id}",
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_foreign_job_id_is_not_found(self) -> None:
        """Иначе по чужому id видно, чем закончился чужой разбор."""
        service = _ServiceStub()

        response = _client(service).get(
            f"/miniapp/api/onboarding/resume-prefill/{uuid4()}",
        )

        assert response.status_code == 404
