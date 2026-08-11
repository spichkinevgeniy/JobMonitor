import hashlib
import hmac
import json
from datetime import UTC, datetime
from urllib.parse import urlencode

from fastapi.testclient import TestClient

from app.application.dto.miniapp.onboarding import OnboardingStateResponse
from app.core.config import config
from app.domain.user.entities import User
from app.domain.user.onboarding import OnboardingStep
from app.telegram.miniapp.app import build_miniapp_app
from app.telegram.miniapp.deps import get_onboarding_service, get_user_service


class _UserServiceStub:
    def __init__(self, user: User) -> None:
        self.user = user

    async def get_user_by_tg_id(self, tg_id: int) -> User | None:
        return self.user if self.user.tg_id.value == tg_id else None


class _OnboardingServiceStub:
    def __init__(self) -> None:
        self.saved_payload = None

    async def get_state(self, tg_id: int) -> OnboardingStateResponse:
        return _empty_state()

    async def save_draft(self, tg_id: int, payload) -> OnboardingStateResponse:
        self.saved_payload = payload
        return _empty_state()

    async def complete(self, tg_id: int) -> OnboardingStateResponse:
        return _empty_state(completed=True)


def _empty_state(completed: bool = False) -> OnboardingStateResponse:
    return OnboardingStateResponse.model_validate(
        {
            "completed": completed,
            "completed_at": None,
            "current_step": "SPECIALTY",
            "max_visited_step": "SPECIALTY",
            "draft": {
                "specialty": None,
                "skills": [],
                "work_formats": None,
                "salary": None,
                "level": None,
            },
        }
    )


def _init_data() -> str:
    payload = {
        "auth_date": str(int(datetime.now(UTC).timestamp())),
        "user": json.dumps({"id": 123, "username": "tester"}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(
        b"WebAppData",
        config.BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()
    payload["hash"] = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(payload)


def _client() -> tuple[TestClient, _OnboardingServiceStub]:
    app = build_miniapp_app()
    onboarding_service = _OnboardingServiceStub()
    app.dependency_overrides[get_user_service] = lambda: _UserServiceStub(User.create(tg_id=123))
    app.dependency_overrides[get_onboarding_service] = lambda: onboarding_service
    return TestClient(app), onboarding_service


def test_onboarding_requires_telegram_header() -> None:
    client, _ = _client()

    response = client.get("/miniapp/api/onboarding")

    assert response.status_code == 401


def test_get_onboarding_uses_telegram_header() -> None:
    client, _ = _client()

    response = client.get(
        "/miniapp/api/onboarding",
        headers={"X-Telegram-Init-Data": _init_data()},
    )

    assert response.status_code == 200
    assert response.json()["current_step"] == OnboardingStep.SPECIALTY.value


def test_patch_is_discriminated_and_returns_full_state() -> None:
    client, service = _client()

    response = client.patch(
        "/miniapp/api/onboarding/draft",
        headers={"X-Telegram-Init-Data": _init_data()},
        json={
            "step": "SPECIALTY",
            "navigate_to": "WORK_FORMAT",
            "data": {"specialty": "Frontend", "skills": ["React"]},
        },
    )

    assert response.status_code == 200
    assert service.saved_payload.step == OnboardingStep.SPECIALTY


def test_patch_rejects_any_combined_with_concrete_format() -> None:
    client, _ = _client()

    response = client.patch(
        "/miniapp/api/onboarding/draft",
        headers={"X-Telegram-Init-Data": _init_data()},
        json={
            "step": "WORK_FORMAT",
            "navigate_to": "SALARY",
            "data": {"work_formats": ["ANY", "REMOTE"]},
        },
    )

    assert response.status_code == 422


def test_complete_uses_header_contract() -> None:
    client, _ = _client()

    response = client.post(
        "/miniapp/api/onboarding/complete",
        headers={"X-Telegram-Init-Data": _init_data()},
    )

    assert response.status_code == 200
    assert response.json()["completed"] is True
