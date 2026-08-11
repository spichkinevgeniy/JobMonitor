from dataclasses import dataclass
from enum import Enum, StrEnum


class WorkFormat(Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"
    UNDEFINED = "UNDEFINED"


class Grade(StrEnum):
    INTERN = "INTERN"
    JUNIOR = "JUNIOR"
    MIDDLE = "MIDDLE"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    UNDEFINED = "UNDEFINED"


class ExperienceLevel(StrEnum):
    NO_EXPERIENCE = "NO_EXPERIENCE"
    ONE_TO_THREE_YEARS = "ONE_TO_THREE_YEARS"
    THREE_TO_SIX_YEARS = "THREE_TO_SIX_YEARS"
    SIX_PLUS_YEARS = "SIX_PLUS_YEARS"
    UNDEFINED = "UNDEFINED"


class CompanyType(StrEnum):
    PRODUCT = "PRODUCT"
    OUTSTAFF = "OUTSTAFF"
    STARTUP = "STARTUP"
    PROJECT_WORK = "PROJECT_WORK"
    UNDEFINED = "UNDEFINED"


class CurrencyType(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class SpecializationType(StrEnum):
    BACKEND = "Backend"
    FRONTEND = "Frontend"
    DATA_SCIENCE_ML = "Data Science / ML"
    MOBILE = "Mobile"
    GAMEDEV = "GameDev"
    QA = "QA"
    INFRASTRUCTURE_DEVOPS = "Infrastructure & DevOps"
    ANALYTICS = "Analytics"
    UI_UX_DESIGN = "UI/UX & Product Design"


class SkillType(StrEnum):
    # Backend
    PYTHON = "Python"
    JAVA_SCALA = "Java/Scala"
    C_SHARP = "C#"
    C_PLUSPLUS = "C++"
    GO = "Go"
    RUST = "Rust"
    C = "C"
    RUBY = "Ruby"
    PHP = "PHP"
    NODE_JS = "Node.js"
    TYPESCRIPT = "TypeScript"
    JAVASCRIPT = "JavaScript"
    KOTLIN = "Kotlin"

    # Frontend
    REACT = "React"
    VUE = "Vue"
    ANGULAR = "Angular"

    # Data Science / ML
    MACHINE_LEARNING = "Machine Learning"
    NLP = "NLP"
    COMPUTER_VISION = "Computer Vision"

    # Mobile
    IOS = "iOS"
    ANDROID = "Android"
    FLUTTER = "Flutter"
    REACT_NATIVE = "React Native"

    # GameDev
    UNITY = "Unity"
    UNREAL_ENGINE = "Unreal Engine"
    GRAPHICS = "Graphics"

    # QA
    MANUAL_QA = "Manual QA"
    QA_AUTOMATION = "QA Automation"

    # Infrastructure & DevOps
    DEVOPS = "DevOps"
    DOCKER = "Docker"
    SRE = "SRE"
    SYSTEM_ADMINISTRATION = "System Administration"

    # Analytics
    SQL = "SQL"
    DATA_ANALYSIS = "Data Analysis"
    DATA_ENGINEERING = "Data Engineering"

    # UI/UX & Product Design
    FIGMA = "Figma"
    PROTOTYPING = "Prototyping"
    UX_RESEARCH = "UX Research"
    DESIGN_SYSTEMS = "Design Systems"
    INTERACTION_DESIGN = "Interaction Design"


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

    @classmethod
    def from_strs(cls, names: list[str]) -> "Skills":
        valid_items: list[SkillType] = []
        for name in names:
            cleaned = name.strip()
            if not cleaned:
                continue
            try:
                valid_items.append(SkillType(cleaned))
            except ValueError:
                continue

        return cls(items=frozenset(valid_items))


@dataclass(frozen=True, slots=True)
class WorkFormats:
    items: frozenset[WorkFormat]

    @classmethod
    def from_values(cls, values: list[WorkFormat]) -> "WorkFormats":
        return cls(items=frozenset(value for value in values if value is not WorkFormat.UNDEFINED))

    @classmethod
    def from_strs(cls, values: list[str]) -> "WorkFormats":
        formats: list[WorkFormat] = []
        for value in values:
            try:
                work_format = WorkFormat(value.strip().upper())
            except ValueError:
                continue
            if work_format is not WorkFormat.UNDEFINED:
                formats.append(work_format)
        return cls.from_values(formats)


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


GRADE_ORDER: dict[Grade, int] = {
    Grade.INTERN: 0,
    Grade.JUNIOR: 1,
    Grade.MIDDLE: 2,
    Grade.SENIOR: 3,
    Grade.LEAD: 4,
    Grade.UNDEFINED: -1,
}


EXPERIENCE_LEVEL_ORDER: dict[ExperienceLevel, int] = {
    ExperienceLevel.NO_EXPERIENCE: 0,
    ExperienceLevel.ONE_TO_THREE_YEARS: 1,
    ExperienceLevel.THREE_TO_SIX_YEARS: 2,
    ExperienceLevel.SIX_PLUS_YEARS: 3,
    ExperienceLevel.UNDEFINED: -1,
}


__all__ = [
    "WorkFormat",
    "Grade",
    "ExperienceLevel",
    "CompanyType",
    "CurrencyType",
    "SpecializationType",
    "SkillType",
    "Specializations",
    "Skills",
    "WorkFormats",
    "Salary",
    "GRADE_ORDER",
    "EXPERIENCE_LEVEL_ORDER",
]
