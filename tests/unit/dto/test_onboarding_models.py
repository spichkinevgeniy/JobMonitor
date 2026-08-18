import pytest
from pydantic import TypeAdapter, ValidationError

from app.application.dto.miniapp import OnboardingDraftRequest
from app.application.dto.miniapp.onboarding import (
    SalaryDraftRequest,
    SpecialtyDraftRequest,
    WorkFormatDraftRequest,
)
from app.domain.shared.value_objects import SpecializationType

adapter = TypeAdapter(OnboardingDraftRequest)


def test_patch_uses_step_discriminator() -> None:
    request = adapter.validate_python(
        {
            "step": "SPECIALTY",
            "navigate_to": "WORK_FORMAT",
            "data": {
                "specializations": ["UI/UX & Product Design", "Frontend"],
                "skills": ["JavaScript", "Docker"],
            },
        }
    )

    assert isinstance(request, SpecialtyDraftRequest)
    assert request.data is not None
    assert request.data.specializations == [
        SpecializationType.UI_UX_DESIGN,
        SpecializationType.FRONTEND,
    ]


def test_specialty_patch_accepts_legacy_singleton_payload() -> None:
    request = adapter.validate_python(
        {
            "step": "SPECIALTY",
            "navigate_to": "WORK_FORMAT",
            "data": {"specialty": "UI/UX & Product Design", "skills": []},
        }
    )

    assert isinstance(request, SpecialtyDraftRequest)
    assert request.data is not None
    assert request.data.specializations == [SpecializationType.UI_UX_DESIGN]


@pytest.mark.parametrize(
    "payload",
    [
        {
            "step": "SPECIALTY",
            "navigate_to": "WORK_FORMAT",
            "data": {"specializations": [], "skills": []},
        },
        {
            "step": "SPECIALTY",
            "navigate_to": "WORK_FORMAT",
            "data": {"specializations": ["Frontend", "Frontend"], "skills": []},
        },
        {
            "step": "WORK_FORMAT",
            "navigate_to": "SALARY",
            "data": {"work_formats": ["ANY", "REMOTE"]},
        },
        {
            "step": "WORK_FORMAT",
            "navigate_to": "SALARY",
            "data": {"work_formats": []},
        },
        {
            "step": "SALARY",
            "navigate_to": "LEVEL",
            "data": {"mode": "FROM", "amount_rub": 0},
        },
        {
            "step": "SALARY",
            "navigate_to": "LEVEL",
            "data": {"mode": "ANY", "amount_rub": 100000},
        },
        {"step": "UNKNOWN", "navigate_to": "LEVEL", "data": {}},
    ],
)
def test_invalid_patch_payload_is_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        adapter.validate_python(payload)


def test_work_format_and_salary_requests_are_typed() -> None:
    work_format = adapter.validate_python(
        {
            "step": "WORK_FORMAT",
            "navigate_to": "SALARY",
            "data": {"work_formats": ["REMOTE", "HYBRID"]},
        }
    )
    salary = adapter.validate_python(
        {
            "step": "SALARY",
            "navigate_to": "LEVEL",
            "data": {"mode": "FROM", "amount_rub": 150000},
        }
    )

    assert isinstance(work_format, WorkFormatDraftRequest)
    assert isinstance(salary, SalaryDraftRequest)


def test_explicit_null_data_is_typed_for_navigation_only_patch() -> None:
    request = adapter.validate_python(
        {
            "step": "WORK_FORMAT",
            "navigate_to": "SPECIALTY",
            "data": None,
        }
    )

    assert isinstance(request, WorkFormatDraftRequest)
    assert request.data is None
