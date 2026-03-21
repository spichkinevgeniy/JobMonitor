import pytest

from app.application.dto.miniapp import SalaryModeChoice, WorkFormatChoice, parse_miniapp_payload
from app.domain.shared import SkillType, SpecializationType


def test_parse_miniapp_payload_accepts_skills_only() -> None:
    payload = parse_miniapp_payload(
        """
        {
          "specializations": ["Backend"],
          "skills": ["Python", "React"],
          "work_format_choice": "REMOTE",
          "salary_mode": "FROM",
          "salary_amount_rub": 200000
        }
        """
    )

    assert payload.specializations == frozenset({SpecializationType.BACKEND})
    assert payload.skills == frozenset({SkillType.PYTHON, SkillType.REACT})
    assert payload.work_format_choice == WorkFormatChoice.REMOTE
    assert payload.salary_mode == SalaryModeChoice.FROM
    assert payload.salary_amount_rub == 200000


def test_parse_miniapp_payload_defaults_to_any_modes() -> None:
    payload = parse_miniapp_payload('{"specializations":["Backend"],"skills":["Python"]}')

    assert payload.work_format_choice == WorkFormatChoice.ANY
    assert payload.salary_mode == SalaryModeChoice.ANY
    assert payload.salary_amount_rub is None


def test_parse_miniapp_payload_rejects_invalid_skill() -> None:
    with pytest.raises(ValueError, match="Invalid mini-app payload"):
        parse_miniapp_payload('{"specializations":["Backend"],"skills":["FastAPI"]}')


def test_parse_miniapp_payload_rejects_invalid_salary_amount() -> None:
    with pytest.raises(ValueError, match="Invalid mini-app payload"):
        parse_miniapp_payload(
            '{"specializations":["Backend"],"skills":["Python"],"salary_amount_rub":"abc"}'
        )
