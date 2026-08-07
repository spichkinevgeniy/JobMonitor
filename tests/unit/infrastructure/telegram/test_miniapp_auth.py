import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import pytest

from app.telegram.miniapp.auth import INIT_DATA_MAX_AGE, validate_init_data

BOT_TOKEN = "test-bot-token"


def build_init_data(auth_date: datetime | None = None, raw_auth_date: str | None = None) -> str:
    if raw_auth_date is None:
        moment = auth_date or datetime.now(UTC)
        raw_auth_date = str(int(moment.timestamp()))

    payload = {
        "auth_date": raw_auth_date,
        "user": json.dumps({"id": 123, "username": "tester"}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    payload["hash"] = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(payload)


def test_validate_init_data_accepts_valid_payload() -> None:
    user_context = validate_init_data(build_init_data(), BOT_TOKEN)

    assert user_context.tg_id == 123
    assert user_context.username == "tester"


def test_validate_init_data_rejects_empty_payload() -> None:
    with pytest.raises(ValueError, match="Пустой initData."):
        validate_init_data("", BOT_TOKEN)


def test_validate_init_data_rejects_invalid_hash() -> None:
    with pytest.raises(ValueError, match="Некорректная подпись initData."):
        validate_init_data(build_init_data() + "broken", BOT_TOKEN)


class TestFreshness:
    def test_rejects_stale_init_data(self) -> None:
        stale = datetime.now(UTC) - INIT_DATA_MAX_AGE - timedelta(minutes=1)

        with pytest.raises(ValueError, match="initData устарел."):
            validate_init_data(build_init_data(stale), BOT_TOKEN)

    def test_accepts_init_data_inside_window(self) -> None:
        recent = datetime.now(UTC) - INIT_DATA_MAX_AGE + timedelta(minutes=5)

        assert validate_init_data(build_init_data(recent), BOT_TOKEN).tg_id == 123

    def test_rejects_missing_auth_date(self) -> None:
        with pytest.raises(ValueError, match="отсутствует auth_date"):
            validate_init_data(build_init_data(raw_auth_date=""), BOT_TOKEN)

    def test_rejects_malformed_auth_date(self) -> None:
        with pytest.raises(ValueError, match="Некорректный auth_date"):
            validate_init_data(build_init_data(raw_auth_date="не-число"), BOT_TOKEN)

    def test_freshness_is_checked_after_signature(self) -> None:
        """Иначе мы отвечаем по-разному на неподписанные данные."""
        stale = datetime.now(UTC) - INIT_DATA_MAX_AGE - timedelta(days=365)

        with pytest.raises(ValueError, match="Некорректная подпись initData."):
            validate_init_data(build_init_data(stale) + "broken", BOT_TOKEN)
