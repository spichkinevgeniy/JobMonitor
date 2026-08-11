from enum import StrEnum
from typing import Protocol


class SkipReason(StrEnum):
    """Почему сообщение не стало вакансией."""

    TOO_SHORT = "too_short"
    NOT_VACANCY = "not_vacancy"
    DUPLICATE = "duplicate"
    NO_SKILLS = "no_skills"
    MIRROR_FAILED = "mirror_failed"
    PARSE_FAILED = "parse_failed"


class Feature(StrEnum):
    """Что нажал пользователь. Метка одна на все фичи, чтобы не плодить метрики."""

    STATS_OPEN = "stats_open"
    EXPORT_JSON = "export_json"
    EXPORT_MARKDOWN = "export_markdown"
    EXPORT_TXT = "export_txt"
    VACANCY_WHY = "vacancy_why"
    VACANCY_REJECT = "vacancy_reject"
    VACANCY_UNDO = "vacancy_undo"
    RESUME_UPLOAD = "resume_upload"
    PROFILE_SAVE = "profile_save"
    ADVICE_SHOWN = "advice_shown"


class IObservabilityService(Protocol):
    def observe_vacancy_collected(self, count: int = 1) -> None: ...

    def observe_not_vacancy_detected(self, count: int = 1) -> None: ...

    def observe_skill_match(self, skill: str, count: int = 1) -> None: ...

    def observe_users_registered(self, count: int = 1) -> None: ...

    def observe_users_snapshot(self, total_users: int, active_users: int) -> None: ...

    def observe_message_skipped(self, reason: SkipReason, count: int = 1) -> None: ...

    def observe_feature_used(self, feature: Feature, count: int = 1) -> None: ...

    def observe_match_rejected(self, reason: str, count: int = 1) -> None: ...
