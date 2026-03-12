from fastapi import FastAPI, Request

from app.application.dto.miniapp import WorkFormatChoice
from app.domain.shared import SkillType, SpecializationType, WorkFormat
from app.telegram.miniapp.page_context import (
    build_format_page_context,
    build_salary_page_context,
    build_skill_options,
    build_skill_sections,
    build_specialization_options,
    build_specialty_page_context,
    build_work_format_options,
)


def test_build_specialization_options_follows_domain_order() -> None:
    assert build_specialization_options() == [item.value for item in SpecializationType]


def test_build_skill_options_follows_domain_order() -> None:
    assert build_skill_options() == [item.value for item in SkillType]


def test_build_skill_sections_groups_current_skills_in_ui_order() -> None:
    sections = build_skill_sections()

    assert [section.title for section in sections] == ["Backend", "Frontend"]
    assert [item.value for item in sections[0].options] == ["Python"]
    assert [item.value for item in sections[1].options] == ["React", "Vue"]


def test_build_skill_sections_cover_every_skill_type_once() -> None:
    sections = build_skill_sections()

    actual_values = [item.value for section in sections for item in section.options]
    assert actual_values == ["Python", "React", "Vue"]
    assert set(actual_values) == {item.value for item in SkillType}


def test_build_work_format_options_uses_domain_values_without_undefined() -> None:
    options = build_work_format_options()

    assert [(item.value, item.label) for item in options] == [
        (WorkFormatChoice.ANY.value, "Любой"),
        (WorkFormat.REMOTE.value, "Удаленка"),
        (WorkFormat.HYBRID.value, "Гибрид"),
        (WorkFormat.ONSITE.value, "Офис"),
    ]


def test_page_context_urls_are_path_only() -> None:
    app = FastAPI()
    app.router.add_api_route("/miniapp/api/specialty", lambda: None, name="miniapp-save-specialty")
    app.router.add_api_route("/miniapp/api/format", lambda: None, name="miniapp-save-format")
    app.router.add_api_route("/miniapp/api/salary", lambda: None, name="miniapp-save-salary")
    request = Request(
        {
            "type": "http",
            "app": app,
            "scheme": "http",
            "method": "GET",
            "path": "/miniapp/specialty",
            "raw_path": b"/miniapp/specialty",
            "root_path": "",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 123),
            "server": ("internal", 8080),
        }
    )

    specialty_context = build_specialty_page_context(request)
    format_context = build_format_page_context(request)
    salary_context = build_salary_page_context(request)

    assert specialty_context["save_url"] == "/miniapp/api/specialty"
    assert format_context["save_url"] == "/miniapp/api/format"
    assert salary_context["save_url"] == "/miniapp/api/salary"
