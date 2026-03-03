import pytest
from app.domain.shared import Specializations, SpecializationType
from app.domain.shared import PrimaryLanguages, LanguageType
from app.domain.shared import TechStack, Salary, CurrencyType


def test_specializations_from_strs_valid():
    input_strings = ["Backend", "BACKEND", "  Frontend  ", "", "InvalidName"]
    result = Specializations.from_strs(input_strings)

    assert isinstance(result, Specializations)
    assert isinstance(result.items, frozenset)

    assert SpecializationType.BACKEND in result.items
    assert SpecializationType.FRONTEND in result.items
    assert len(result.items) == 2


def test_primary_languages_from_strs_valid():
    input_strings = ["Python", " Go ", "", "dsadasd"]
    result = PrimaryLanguages.from_strs(input_strings)

    assert isinstance(result, PrimaryLanguages)
    assert isinstance(result.items, frozenset)

    assert LanguageType.PYTHON in result.items
    assert LanguageType.GO in result.items
    assert len(result.items) == 2


@pytest.mark.parametrize(
    "input_data, expected",
    [
        ([" python ", "js"], {"Python", "Js"}),
        ([], set()),
        (None, set()),
        (["", "  "], set()),
        (["python", "python", "PYTHON"], {"Python"}),
    ],
)
def test_tech_stack_behavior(input_data, expected):
    stack = TechStack.create(input_data)
    assert stack.items == frozenset(expected)


@pytest.mark.parametrize(
    "amount, currency_input, expected_currency",
    [
        (100000, "RUB", CurrencyType.RUB),
        (5000, "usd", CurrencyType.USD),
        (3000, "  eUr  ", CurrencyType.EUR),
        (1500, "  ", None),
        (2000, None, None),
        (None, None, None),
    ],
)
def test_salary_create_success(amount, currency_input, expected_currency):
    salary = Salary.create(amount=amount, currency=currency_input)

    assert salary.amount == amount
    assert salary.currency == expected_currency


def test_salary_negative_amount():
    with pytest.raises(ValueError):
        Salary.create(amount=-1, currency="USD")
