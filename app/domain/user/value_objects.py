from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class UserId:
    value: int


class FilterMode(StrEnum):
    STRICT = "STRICT"
    SOFT = "SOFT"


class LevelFilterMode(StrEnum):
    IGNORE = "IGNORE"
    UP_TO = "UP_TO"
    EXACT = "EXACT"
