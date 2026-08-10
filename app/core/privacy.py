import hashlib
import hmac
from pathlib import PurePosixPath

from app.core.config import config

USER_REF_LENGTH = 12
UNKNOWN_REF = "anon"
UNKNOWN_EXT = "none"
MAX_EXT_LENGTH = 10


def user_ref(tg_id: int | None) -> str:
    """Псевдоним пользователя для логов вместо tg_id.

    Стабилен для одного человека, поэтому строки лога связываются в историю,
    но в Telegram-аккаунт не разворачивается.
    """
    if tg_id is None:
        return UNKNOWN_REF
    digest = hmac.new(
        config.TELEMETRY_SALT.encode("utf-8"),
        str(tg_id).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:USER_REF_LENGTH]


def file_ext(file_name: str | None) -> str:
    """Расширение вместо имени файла: резюме люди называют своим ФИО."""
    if not file_name:
        return UNKNOWN_EXT
    suffix = PurePosixPath(file_name).suffix.lstrip(".").lower()
    # isalnum() пропускает кириллицу, а «расширение» из букв имени — тот же
    # лишний текст, от которого мы избавляемся.
    if not suffix or len(suffix) > MAX_EXT_LENGTH:
        return UNKNOWN_EXT
    if not (suffix.isascii() and suffix.isalnum()):
        return UNKNOWN_EXT
    return suffix
