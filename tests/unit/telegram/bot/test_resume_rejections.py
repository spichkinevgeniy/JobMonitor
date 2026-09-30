"""Отказы при загрузке резюме: какой ответ получает человек на каждую ошибку."""

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest

from app.application.ports.llm_port import LLMUnavailableError
from app.infrastructure.parsers import NotAResumeError, ParserError, TooManyPagesError
from app.telegram.bot.routers import resume as resume_router
from app.telegram.bot.views import (
    build_resume_llm_unavailable_text,
    build_resume_not_a_resume_text,
    build_resume_parser_error_text,
    build_resume_too_many_pages_text,
    build_resume_unknown_error_text,
    build_resume_unsupported_format_text,
)


class RecordingUpload:
    """Вместо загрузки — запись того, что ушло бы пользователю."""

    def __init__(self) -> None:
        self.replies: list[str] = []
        self.tg_id = 777
        self.document = SimpleNamespace(file_name="cv.pdf", file_size=1024)
        self.log_fields: dict[str, Any] = {"user": "u", "file_ext": ".pdf", "file_size": 1024}

    async def reset_to_menu(self, text: str) -> None:
        self.replies.append(text)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ValueError("Extension .doc is not supported"), build_resume_unsupported_format_text),
        # Наследники ParserError обязаны получить свой ответ, а не общий.
        (NotAResumeError("not a resume"), build_resume_not_a_resume_text),
        (TooManyPagesError("too many pages"), build_resume_too_many_pages_text),
        (ParserError("broken pdf"), build_resume_parser_error_text),
        (LLMUnavailableError("down"), build_resume_llm_unavailable_text),
        (RuntimeError("boom"), build_resume_unknown_error_text),
    ],
)
async def test_each_error_gets_its_reply(error: Exception, expected: Callable[[], str]) -> None:
    upload = RecordingUpload()

    await resume_router._reject(upload, error)  # type: ignore[arg-type]

    assert upload.replies == [expected()]


class TestUploadGuard:
    def setup_method(self) -> None:
        resume_router._active_resume_uploads.clear()

    def test_second_upload_of_same_user_is_refused(self) -> None:
        assert resume_router._claim_upload(1) is True
        assert resume_router._claim_upload(1) is False

    def test_release_frees_the_slot(self) -> None:
        resume_router._claim_upload(1)
        resume_router._release_upload(1)

        assert resume_router._claim_upload(1) is True

    def test_unknown_user_is_never_blocked(self) -> None:
        assert resume_router._claim_upload(None) is True
        assert resume_router._claim_upload(None) is True
