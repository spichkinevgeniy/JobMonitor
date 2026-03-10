from dataclasses import dataclass
from enum import Enum, StrEnum


class WorkFormat(Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"
    UNDEFINED = "UNDEFINED"


class CurrencyType(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class SpecializationType(StrEnum):
    BACKEND = "Backend"
    FRONTEND = "Frontend"
    FULLSTACK = "Fullstack"
    MOBILE = "Mobile"
    DEVOPS = "DevOps"
    DATA_SCIENCE = "Data Science"
    QA = "QA"
    MANAGEMENT = "Management"


class SkillType(StrEnum):
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    REACT = "React"
    VUE = "Vue"


@dataclass(frozen=True, slots=True)
class Specializations:
    items: frozenset[SpecializationType]

    @classmethod
    def from_strs(cls, names: list[str]) -> "Specializations":
        valid_items = []
        for name in names:
            try:
                valid_items.append(SpecializationType(name.strip()))
            except ValueError:
                continue

        return cls(items=frozenset(valid_items))


@dataclass(frozen=True, slots=True)
class Skills:
    items: frozenset[SkillType]

    _ALIASES = {
        "python": SkillType.PYTHON,
        "javascript": SkillType.JAVASCRIPT,
        "react": SkillType.REACT,
        "vue": SkillType.VUE,
    }

    @classmethod
    def from_strs(cls, names: list[str]) -> "Skills":
        valid_items: list[SkillType] = []
        for name in names:
            normalized = cls._normalize_name(name)
            if normalized is None:
                continue
            valid_items.append(normalized)

        return cls(items=frozenset(valid_items))

    @classmethod
    def _normalize_name(cls, raw_name: str) -> SkillType | None:
        cleaned = raw_name.strip()
        if not cleaned:
            return None

        try:
            return SkillType(cleaned)
        except ValueError:
            return cls._ALIASES.get(cleaned.lower())


@dataclass(frozen=True, slots=True)
class Salary:
    amount: int | None
    currency: CurrencyType | None

    @classmethod
    def create(cls, amount: int | None = None, currency: str | None = None) -> "Salary":
        if amount is not None and amount < 0:
            raise ValueError("Salary cannot be negative")

        if amount is None:
            return cls(amount=None, currency=None)

        if currency is None or not currency.strip():
            return cls(amount=amount, currency=CurrencyType.RUB)

        normalized_currency = currency.upper().strip()
        if normalized_currency != CurrencyType.RUB.value:
            return cls(amount=None, currency=None)

        return cls(
            amount=amount,
            currency=CurrencyType.RUB,
        )


__all__ = [
    "WorkFormat",
    "CurrencyType",
    "SpecializationType",
    "SkillType",
    "Specializations",
    "Skills",
    "Salary",
]
