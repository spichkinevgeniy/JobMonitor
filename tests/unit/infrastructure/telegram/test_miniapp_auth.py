import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest

from app.telegram.miniapp.auth import validate_init_data


def test_validate_init_data_accepts_valid_payload() -> None:
    init_data = build_init_data()

    user_context = validate_init_data(init_data, "test-bot-token")

    assert user_context.tg_id == 123
    assert user_context.username == "tester"


def test_validate_init_data_rejects_empty_payload() -> None:
    with pytest.raises(ValueError, match="Пустой initData."):
        validate_init_data("", "test-bot-token")


def test_validate_init_data_rejects_invalid_hash() -> None:
    invalid_init_data = build_init_data() + "broken"

    with pytest.raises(ValueError, match="Некорректная подпись initData."):
        validate_init_data(invalid_init_data, "test-bot-token")


def build_init_data() -> str:
    payload = {
        "auth_date": "1700000000",
        "user": json.dumps({"id": 123, "username": "tester"}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(
        b"WebAppData",
        b"test-bot-token",
        hashlib.sha256,
    ).digest()
    payload["hash"] = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(payload)
