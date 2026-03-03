import json
from pathlib import Path
from typing import Any, Literal

from pydantic import computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    APP_ENV: Literal["development", "production"] = "development"

    API_ID: int
    API_HASH: str
    TELEGRAM_PHONE: str | None = None
    TELETHON_LOGIN_MODE: str = "qr"
    TELEGRAM_2FA_PASSWORD: str | None = None
    BOT_TOKEN: str
    CHANNELS_MAP_PATH: str = "channels_map.json"
    MIRROR_CHANNEL: int

    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    GOOGLE_API_KEY: str
    GOOGLE_MODEL: str = "gemini-2.5-flash"

    SENTRY_DSN: str | None = None
    SENTRY_ENV: str
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0

    LOGFIRE_ENABLED: bool = True
    LOGFIRE_TOKEN: str | None = None
    LOGFIRE_SERVICE_NAME: str
    LOGFIRE_ENV: str

    METRICS_ENABLED: bool = True
    METRICS_ADDR: str = "0.0.0.0"
    METRICS_PORT: int = 8000

    @computed_field
    @property
    def ASYNC_SQLALCHEMY_DATABASE_URI(self) -> str:
        return str(
            MultiHostUrl.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    @property
    def _channels_groups(self) -> dict[str, list[str]]:
        path = Path(self.CHANNELS_MAP_PATH)
        if not path.exists():
            raise FileNotFoundError(f"Channels map file not found: {path}")

        raw: Any = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Channels map must be a JSON object")

        parsed: dict[str, list[str]] = {}
        for group_name, channels in raw.items():
            if not isinstance(group_name, str):
                raise ValueError("Channels map keys must be strings")
            if not isinstance(channels, list):
                raise ValueError(f"Group '{group_name}' must contain a list of channels")

            cleaned_channels: list[str] = []
            for channel in channels:
                if not isinstance(channel, str):
                    raise ValueError(f"Channel in group '{group_name}' must be a string")
                normalized = channel.strip()
                if normalized:
                    cleaned_channels.append(normalized)
            parsed[group_name] = cleaned_channels

        return parsed

    @computed_field
    @property
    def CHANNELS_GROUPS(self) -> dict[str, list[str]]:
        return self._channels_groups

    @computed_field
    @property
    def CHANNELS(self) -> list[str]:
        seen: set[str] = set()
        flattened: list[str] = []
        for channels in self._channels_groups.values():
            for channel in channels:
                if channel in seen:
                    continue
                seen.add(channel)
                flattened.append(channel)
        return flattened

    def validate_runtime(self) -> None:
        if self.APP_ENV != "production":
            return

        required_strings = {
            "API_HASH": self.API_HASH,
            "BOT_TOKEN": self.BOT_TOKEN,
            "GOOGLE_API_KEY": self.GOOGLE_API_KEY,
            "POSTGRES_SERVER": self.POSTGRES_SERVER,
            "POSTGRES_USER": self.POSTGRES_USER,
            "POSTGRES_PASSWORD": self.POSTGRES_PASSWORD,
            "POSTGRES_DB": self.POSTGRES_DB,
        }
        missing: list[str] = []
        for key, value in required_strings.items():
            if _is_missing_or_placeholder(value):
                missing.append(key)

        if self.API_ID <= 0:
            missing.append("API_ID")
        if self.POSTGRES_PORT <= 0:
            missing.append("POSTGRES_PORT")
        if self.MIRROR_CHANNEL == 0:
            missing.append("MIRROR_CHANNEL")

        if missing:
            joined = ", ".join(sorted(set(missing)))
            raise ValueError(
                "Invalid production configuration. Set valid values for: "
                f"{joined}"
            )


class LocalAppSettings(BaseAppSettings):
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5433
    SENTRY_ENV: str = "development"
    LOGFIRE_ENV: str = "development"


class DockerAppSettings(BaseAppSettings):
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    SENTRY_ENV: str = "production"
    LOGFIRE_ENV: str = "production"


def _is_missing_or_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return True

    placeholders = (
        "your_",
        "you_api_key",
        "example",
        "changeme",
        "change_me",
        "<",
        ">",
    )
    return any(marker in normalized for marker in placeholders)


def load_settings() -> BaseAppSettings:
    settings = LocalAppSettings()
    if settings.APP_ENV == "production":
        return DockerAppSettings()
    return settings


config = load_settings()
