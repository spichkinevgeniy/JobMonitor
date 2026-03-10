import pytest

from app.domain.shared import CurrencyType, Salary, Skills, SkillType, SpecializationType, Specializations


def test_specializations_from_strs_valid() -> None:
    input_strings = ["Backend", "Backend", "  Frontend  ", "", "InvalidName"]
    result = Specializations.from_strs(input_strings)

    assert isinstance(result, Specializations)
    assert isinstance(result.items, frozenset)
    assert SpecializationType.BACKEND in result.items
    assert SpecializationType.FRONTEND in result.items
    assert len(result.items) == 2


def test_skills_from_strs_valid_and_deduplicated() -> None:
    input_strings = ["Python", " python ", "React", "invalid", "", "VUE"]
    result = Skills.from_strs(input_strings)

    assert isinstance(result, Skills)
    assert isinstance(result.items, frozenset)
    assert result.items == frozenset(
        {SkillType.PYTHON, SkillType.REACT, SkillType.VUE}
    )


@pytest.mark.parametrize(
    ("amount", "currency_input", "expected_amount", "expected_currency"),
    [
        (100000, "RUB", 100000, CurrencyType.RUB),
        (5000, "usd", None, None),
        (3000, "  eUr  ", None, None),
        (1500, "  ", 1500, CurrencyType.RUB),
        (2000, None, 2000, CurrencyType.RUB),
        (None, None, None, None),
    ],
)
def test_salary_create_success(
    amount: int | None,
    currency_input: str | None,
    expected_amount: int | None,
    expected_currency: CurrencyType | None,
) -> None:
    salary = Salary.create(amount=amount, currency=currency_input)

    assert salary.amount == expected_amount
    assert salary.currency == expected_currency


def test_salary_negative_amount() -> None:
    with pytest.raises(ValueError):
        Salary.create(amount=-1, currency="RUB")
