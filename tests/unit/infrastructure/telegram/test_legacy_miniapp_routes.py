import hashlib
import hmac
import json
from datetime import UTC, datetime
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from app.application.dto.miniapp import (
    FormatSaveRequest,
    LevelSaveRequest,
    SalarySaveRequest,
    SpecialtySaveRequest,
)
from app.core.config import config
from app.domain.shared import Grade, WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, LevelFilterMode
from app.telegram.miniapp.app import build_miniapp_app
from app.telegram.miniapp.deps import get_user_service


class _LegacyUserServiceStub:
    def __init__(self) -> None:
        self.user = User.create(
            tg_id=123,
            cv_specializations_raw=["Backend"],
            cv_skills_raw=["Python"],
            cv_salary_amount=150000,
            cv_salary_currency="RUB",
            filter_salary_mode=FilterMode.STRICT,
            cv_grade=Grade.JUNIOR,
            filter_grade_mode=LevelFilterMode.EXACT,
            cv_work_format=WorkFormat.REMOTE,
            filter_work_format_mode=FilterMode.STRICT,
        )

    async def get_user_by_tg_id(self, tg_id: int) -> User | None:
        return self.user if tg_id == self.user.tg_id.value else None

    async def update_profile_specializations_and_skills(self, **kwargs: object) -> bool:
        return True

    async def update_profile_work_format_filter(self, **kwargs: object) -> bool:
        return True

    async def update_profile_salary_filter(self, **kwargs: object) -> bool:
        return True

    async def update_profile_level_filters(self, **kwargs: object) -> bool:
        return True


def _init_data() -> str:
    payload = {
        "auth_date": str(int(datetime.now(UTC).timestamp())),
        "user": json.dumps({"id": 123, "username": "tester"}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
    payload["hash"] = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(payload)


def _client() -> TestClient:
    app = build_miniapp_app()
    service = _LegacyUserServiceStub()
    app.dependency_overrides[get_user_service] = lambda: service
    return TestClient(app)


def test_legacy_request_contracts_still_require_body_init_data() -> None:
    assert "init_data" in SpecialtySaveRequest.model_fields
    assert "init_data" in FormatSaveRequest.model_fields
    assert "init_data" in SalarySaveRequest.model_fields
    assert "init_data" in LevelSaveRequest.model_fields


def test_legacy_request_contracts_have_not_acquired_onboarding_fields() -> None:
    onboarding_fields = {"step", "navigate_to", "data"}

    assert onboarding_fields.isdisjoint(SpecialtySaveRequest.model_fields)
    assert onboarding_fields.isdisjoint(FormatSaveRequest.model_fields)
    assert onboarding_fields.isdisjoint(SalarySaveRequest.model_fields)
    assert onboarding_fields.isdisjoint(LevelSaveRequest.model_fields)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (
            "/miniapp/api/specialty",
            {"specializations": ["Backend"], "skills": ["Python"]},
        ),
        ("/miniapp/api/format", {"work_format_choice": "REMOTE"}),
        (
            "/miniapp/api/salary",
            {"salary_mode": "FROM", "salary_amount_rub": 150000},
        ),
        (
            "/miniapp/api/level",
            {
                "grade_mode": "EXACT",
                "grade_choice": "JUNIOR",
                "experience_mode": "IGNORE",
                "experience_level_choice": "ANY",
            },
        ),
    ],
)
def test_legacy_get_contracts_are_unchanged(path: str, expected: dict[str, object]) -> None:
    response = _client().get(
        path,
        headers={"X-Telegram-Init-Data": _init_data()},
    )

    assert response.status_code == 200
    assert response.json() == expected


@pytest.mark.parametrize(
    ("path", "payload", "message"),
    [
        (
            "/miniapp/api/specialty",
            {"specializations": ["Backend"], "skills": ["Python"]},
            "Специализации и скиллы сохранены.",
        ),
        (
            "/miniapp/api/format",
            {"work_format_choice": "REMOTE"},
            "Формат сохранен.",
        ),
        (
            "/miniapp/api/salary",
            {"salary_mode": "FROM", "salary_amount_rub": 150000},
            "Зарплата сохранена.",
        ),
        (
            "/miniapp/api/level",
            {
                "grade_mode": "EXACT",
                "grade_choice": "JUNIOR",
                "experience_mode": "IGNORE",
                "experience_level_choice": "ANY",
            },
            "Грейд и опыт сохранены.",
        ),
    ],
)
def test_legacy_post_contracts_are_unchanged(
    path: str,
    payload: dict[str, object],
    message: str,
) -> None:
    response = _client().post(path, json={"init_data": _init_data(), **payload})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": message}
