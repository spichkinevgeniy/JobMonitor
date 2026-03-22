from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.application.dto.miniapp import (
    ExperienceLevelChoice,
    FormatReadResponse,
    FormatSaveRequest,
    GradeChoice,
    LevelReadResponse,
    LevelSaveRequest,
    SalaryModeChoice,
    SalaryReadResponse,
    SalarySaveRequest,
    SaveResponse,
    SpecialtyReadResponse,
    SpecialtySaveRequest,
    WorkFormatChoice,
)
from app.application.services.user_service import UserService
from app.domain.shared.value_objects import ExperienceLevel, Grade, WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode
from app.telegram.miniapp.deps import get_current_user, get_user_service, parse_user_context
from app.telegram.miniapp.page_context import (
    build_format_page_context,
    build_level_page_context,
    build_salary_page_context,
    build_specialty_page_context,
)
from app.telegram.miniapp.ui import templates

router = APIRouter()


@router.get("/miniapp", include_in_schema=False)
async def miniapp_index() -> RedirectResponse:
    return RedirectResponse(url="/miniapp/specialty", status_code=307)


@router.get("/miniapp/specialty", response_class=HTMLResponse, name="miniapp-specialty")
async def specialty_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "pages/specialty.html",
        build_specialty_page_context(request),
    )


@router.get("/miniapp/format", response_class=HTMLResponse, name="miniapp-format")
async def format_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "pages/format.html",
        build_format_page_context(request),
    )


@router.get("/miniapp/salary", response_class=HTMLResponse, name="miniapp-salary")
async def salary_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "pages/salary.html",
        build_salary_page_context(request),
    )


@router.get("/miniapp/level", response_class=HTMLResponse, name="miniapp-level")
async def level_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "pages/level.html",
        build_level_page_context(request),
    )


@router.get(
    "/miniapp/api/specialty",
    name="miniapp-read-specialty",
    response_model=SpecialtyReadResponse,
)
async def read_specialty(
    user: Annotated[User, Depends(get_current_user)],
) -> SpecialtyReadResponse:
    return SpecialtyReadResponse(
        specializations=sorted(item.value for item in user.cv_specializations.items),
        skills=sorted(item.value for item in user.cv_skills.items),
    )


@router.post(
    "/miniapp/api/specialty",
    name="miniapp-save-specialty",
    response_model=SaveResponse,
)
async def save_specialty(
    payload: SpecialtySaveRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> SaveResponse:
    user_context = parse_user_context(payload.init_data)
    if not payload.specializations:
        raise HTTPException(status_code=400, detail="Выберите минимум одну специализацию.")
    if not payload.skills:
        raise HTTPException(status_code=400, detail="Выберите минимум один скилл.")

    updated = await service.update_profile_specializations_and_skills(
        tg_id=user_context.tg_id,
        specializations=[item.value for item in payload.specializations],
        skills=[item.value for item in payload.skills],
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")

    return SaveResponse(message="Специализации и скиллы сохранены.")


@router.get(
    "/miniapp/api/format",
    name="miniapp-read-format",
    response_model=FormatReadResponse,
)
async def read_format(
    user: Annotated[User, Depends(get_current_user)],
) -> FormatReadResponse:
    return FormatReadResponse(work_format_choice=_work_format_choice(user))


@router.post(
    "/miniapp/api/format",
    name="miniapp-save-format",
    response_model=SaveResponse,
)
async def save_format(
    payload: FormatSaveRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> SaveResponse:
    user_context = parse_user_context(payload.init_data)

    if payload.work_format_choice == WorkFormatChoice.ANY:
        work_format = None
        work_format_mode = FilterMode.SOFT
    else:
        work_format = WorkFormat(payload.work_format_choice.value)
        work_format_mode = FilterMode.STRICT

    updated = await service.update_profile_work_format_filter(
        tg_id=user_context.tg_id,
        work_format=work_format,
        work_format_mode=work_format_mode,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")

    return SaveResponse(message="Формат сохранен.")


@router.get(
    "/miniapp/api/salary",
    name="miniapp-read-salary",
    response_model=SalaryReadResponse,
)
async def read_salary(
    user: Annotated[User, Depends(get_current_user)],
) -> SalaryReadResponse:
    return SalaryReadResponse(
        salary_mode=_salary_mode_choice(user),
        salary_amount_rub=_salary_amount_value(user),
    )


@router.post(
    "/miniapp/api/salary",
    name="miniapp-save-salary",
    response_model=SaveResponse,
)
async def save_salary(
    payload: SalarySaveRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> SaveResponse:
    user_context = parse_user_context(payload.init_data)

    if payload.salary_mode == SalaryModeChoice.FROM:
        if payload.salary_amount_rub is None or payload.salary_amount_rub <= 0:
            raise HTTPException(status_code=400, detail="Укажите зарплату больше 0.")
        salary_amount_rub = payload.salary_amount_rub
        salary_mode = FilterMode.STRICT
    else:
        salary_amount_rub = None
        salary_mode = FilterMode.SOFT

    updated = await service.update_profile_salary_filter(
        tg_id=user_context.tg_id,
        salary_amount_rub=salary_amount_rub,
        salary_mode=salary_mode,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")

    return SaveResponse(message="Зарплата сохранена.")


@router.get(
    "/miniapp/api/level",
    name="miniapp-read-level",
    response_model=LevelReadResponse,
)
async def read_level(
    user: Annotated[User, Depends(get_current_user)],
) -> LevelReadResponse:
    return LevelReadResponse(
        grade_choice=_grade_choice(user),
        experience_level_choice=_experience_level_choice(user),
    )


@router.post(
    "/miniapp/api/level",
    name="miniapp-save-level",
    response_model=SaveResponse,
)
async def save_level(
    payload: LevelSaveRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> SaveResponse:
    user_context = parse_user_context(payload.init_data)

    grade, grade_mode = _grade_from_choice(payload.grade_choice)
    experience_level, experience_mode = _experience_level_from_choice(
        payload.experience_level_choice
    )

    updated = await service.update_profile_level_filters(
        tg_id=user_context.tg_id,
        grade=grade,
        grade_mode=grade_mode,
        experience_level=experience_level,
        experience_mode=experience_mode,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")

    return SaveResponse(message="Грейд и опыт сохранены.")


def _work_format_choice(user: User) -> str:
    if (
        user.filter_work_format_mode != FilterMode.STRICT
        or user.cv_work_format is None
        or user.cv_work_format == WorkFormat.UNDEFINED
    ):
        return WorkFormatChoice.ANY.value
    return str(user.cv_work_format.value)


def _salary_mode_choice(user: User) -> str:
    if (
        user.filter_salary_mode == FilterMode.STRICT
        and user.cv_salary is not None
        and user.cv_salary.amount is not None
    ):
        return SalaryModeChoice.FROM.value
    return SalaryModeChoice.ANY.value


def _salary_amount_value(user: User) -> int | None:
    if user.filter_salary_mode != FilterMode.STRICT:
        return None
    if user.cv_salary is None or user.cv_salary.amount is None:
        return None
    return user.cv_salary.amount


def _grade_choice(user: User) -> str:
    if user.filter_grade_mode != FilterMode.STRICT or user.cv_grade is None:
        return GradeChoice.ANY.value
    return user.cv_grade.value


def _experience_level_choice(user: User) -> str:
    if user.filter_experience_mode != FilterMode.STRICT or user.cv_experience_level is None:
        return ExperienceLevelChoice.ANY.value
    return user.cv_experience_level.value


def _grade_from_choice(choice: GradeChoice) -> tuple[Grade | None, FilterMode]:
    if choice == GradeChoice.ANY:
        return None, FilterMode.SOFT
    return Grade(choice.value), FilterMode.STRICT


def _experience_level_from_choice(
    choice: ExperienceLevelChoice,
) -> tuple[ExperienceLevel | None, FilterMode]:
    if choice == ExperienceLevelChoice.ANY:
        return None, FilterMode.SOFT
    return ExperienceLevel(choice.value), FilterMode.STRICT
