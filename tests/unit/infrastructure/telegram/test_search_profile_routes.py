import hashlib
import hmac
import json
from datetime import UTC, datetime
from urllib.parse import urlencode

from fastapi.testclient import TestClient

from app.core.config import config
from app.domain.shared import Grade
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, LevelFilterMode
from app.telegram.miniapp.app import build_miniapp_app
from app.telegram.miniapp.deps import get_user_service


class _UserServiceStub:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def get_user_by_tg_id(self, tg_id: int) -> User | None:
        if self.user is None or self.user.tg_id.value != tg_id:
            return None
        return self.user


def _completed_user() -> User:
    return User.create(
        tg_id=123,
        cv_specializations_raw=["Frontend"],
        cv_skills_raw=["React", "TypeScript"],
        cv_work_formats_raw=["REMOTE", "HYBRID"],
        cv_salary_amount=150000,
        cv_salary_currency="RUB",
        filter_salary_mode=FilterMode.STRICT,
        cv_grade=Grade.JUNIOR,
        filter_grade_mode=LevelFilterMode.AT_LEAST,
        onboarding_completed_at=datetime.now(UTC),
        is_active=True,
    )


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


def _client(user: User | None) -> TestClient:
    app = build_miniapp_app()
    app.dependency_overrides[get_user_service] = lambda: _UserServiceStub(user)
    return TestClient(app)


def test_search_profile_requires_valid_telegram_header() -> None:
    assert _client(_completed_user()).get("/miniapp/api/search-profile").status_code == 401
    response = _client(_completed_user()).get(
        "/miniapp/api/search-profile",
        headers={"X-Telegram-Init-Data": "invalid"},
    )
    assert response.status_code == 401


def test_completed_user_receives_explicit_search_profile() -> None:
    response = _client(_completed_user()).get(
        "/miniapp/api/search-profile",
        headers={"X-Telegram-Init-Data": _init_data()},
    )

    assert response.status_code == 200
    assert response.json() == {
        "specializations": ["Frontend"],
        "skills": ["React", "TypeScript"],
        "work_formats": ["HYBRID", "REMOTE"],
        "salary": {"mode": "FROM", "amount_rub": 150000},
        "level": {"grade": "JUNIOR", "mode": "AT_LEAST"},
        "search_active": True,
    }


def test_nonexistent_user_returns_not_found() -> None:
    response = _client(None).get(
        "/miniapp/api/search-profile",
        headers={"X-Telegram-Init-Data": _init_data()},
    )

    assert response.status_code == 404


def test_incomplete_user_returns_conflict() -> None:
    response = _client(User.create(tg_id=123)).get(
        "/miniapp/api/search-profile",
        headers={"X-Telegram-Init-Data": _init_data()},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Профиль поиска ещё не завершён."}
