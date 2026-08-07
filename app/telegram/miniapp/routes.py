from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.application.dto.miniapp import (
    ExperienceLevelChoice,
    ExportRequest,
    FormatReadResponse,
    FormatSaveRequest,
    GradeChoice,
    LevelModeChoice,
    LevelReadResponse,
    LevelSaveRequest,
    ProfileStatsResponse,
    SalaryModeChoice,
    SalaryReadResponse,
    SalarySaveRequest,
    SaveResponse,
    SpecialtyReadResponse,
    SpecialtySaveRequest,
    StatsCompanyTypeResponse,
    StatsExportResponse,
    StatsFunnelResponse,
    StatsFunnelRowResponse,
    StatsTrendPointResponse,
    StatsTrendSeriesResponse,
    WorkFormatChoice,
)
from app.application.services.export_service import ExportFormat, ExportService
from app.application.services.stats_service import (
    FilterFunnel,
    ProfileStats,
    StatsService,
    TrendGranularity,
)
from app.application.services.user_service import UserService
from app.domain.matching.entities import MatchRejectionReason
from app.domain.shared.value_objects import ExperienceLevel, Grade, WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode, LevelFilterMode
from app.infrastructure.notifications import TelegramDocumentSender
from app.telegram.miniapp.deps import (
    get_current_user,
    get_document_sender,
    get_export_service,
    get_stats_service,
    get_user_service,
    parse_user_context,
)
from app.telegram.miniapp.page_context import (
    build_format_page_context,
    build_level_page_context,
    build_salary_page_context,
    build_specialty_page_context,
    build_stats_page_context,
    company_type_label,
)
from app.telegram.miniapp.throttle import (
    cancel_export,
    register_export,
    seconds_until_export_allowed,
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


@router.get("/miniapp/stats", response_class=HTMLResponse, name="miniapp-stats")
async def stats_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "pages/stats.html",
        build_stats_page_context(request),
    )


@router.get(
    "/miniapp/api/stats",
    name="miniapp-read-stats",
    response_model=ProfileStatsResponse,
)
async def read_stats(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[StatsService, Depends(get_stats_service)],
    export_service: Annotated[ExportService, Depends(get_export_service)],
) -> ProfileStatsResponse:
    stats = await service.build_profile_stats(user)
    export_count, export_since = await export_service.count_available(user.tg_id.value)
    return _to_stats_response(user, stats, export_count, export_since)


@router.post(
    "/miniapp/api/export",
    name="miniapp-export",
    response_model=SaveResponse,
)
async def export_vacancies(
    payload: ExportRequest,
    service: Annotated[ExportService, Depends(get_export_service)],
    sender: Annotated[TelegramDocumentSender, Depends(get_document_sender)],
) -> SaveResponse:
    user_context = parse_user_context(payload.init_data)

    try:
        export_format = ExportFormat(payload.export_format)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неизвестный формат выгрузки.") from None

    # Проверка и отметка без await между ними, иначе пачка запросов пройдёт целиком.
    retry_after = seconds_until_export_allowed(user_context.tg_id)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail=f"Слишком часто. Повторите через {retry_after} с.",
        )
    register_export(user_context.tg_id)

    export_file = await service.build(user_context.tg_id, export_format)
    if export_file is None:
        cancel_export(user_context.tg_id)
        raise HTTPException(
            status_code=404,
            detail="Пока нечего выгружать: бот ещё не присылал вам вакансии.",
        )

    await sender.send_document(
        user_tg_id=user_context.tg_id,
        filename=export_file.filename,
        content=export_file.content,
        caption=f"Выгрузка вакансий: {export_file.count} шт.",
    )
    return SaveResponse(message="Файл отправлен в чат с ботом.")


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
        grade_mode=_level_mode_choice(user.filter_grade_mode),
        grade_choice=_grade_choice(user),
        experience_mode=_level_mode_choice(user.filter_experience_mode),
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

    grade, grade_mode = _grade_filter_from_payload(payload.grade_choice, payload.grade_mode)
    experience_level, experience_mode = _experience_filter_from_payload(
        payload.experience_level_choice,
        payload.experience_mode,
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


_TREND_TOGGLE_LABELS = {
    TrendGranularity.WEEK: "Недели",
    TrendGranularity.DAY: "Дни",
}
_REJECTION_LABELS = {
    MatchRejectionReason.SALARY: "Отсёк фильтр зарплаты",
    MatchRejectionReason.GRADE: "Отсёк грейд",
    MatchRejectionReason.EXPERIENCE: "Отсёк опыт",
    MatchRejectionReason.FORMAT: "Отсёк формат работы",
}
# Бакеты скользящие (от «сейчас» назад), а не календарные, поэтому пишем
# «за последние 7 дней», а не «за эту неделю».
_TREND_HEADLINE_LABELS = {
    TrendGranularity.WEEK: "за последние 7 дней",
    TrendGranularity.DAY: "за последние сутки",
}


_MONTHS_GENITIVE = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def _since_label(since: datetime | None) -> str | None:
    if since is None:
        return None
    return f"с {since.day} {_MONTHS_GENITIVE[since.month - 1]}"


def _to_stats_response(
    user: User,
    stats: ProfileStats,
    export_count: int,
    export_since: datetime | None,
) -> ProfileStatsResponse:
    return ProfileStatsResponse(
        has_profile=bool(user.cv_specializations.items and user.cv_skills.items),
        has_data=_has_any_data(stats),
        export=StatsExportResponse(
            count=export_count,
            since_label=_since_label(export_since),
        ),
        trends=[
            StatsTrendSeriesResponse(
                granularity=series.granularity.value,
                toggle_label=_TREND_TOGGLE_LABELS[series.granularity],
                headline_label=_TREND_HEADLINE_LABELS[series.granularity],
                points=[
                    StatsTrendPointResponse(
                        label=point.bucket_start.strftime("%d.%m"),
                        count=point.count,
                    )
                    for point in series.points
                ],
            )
            for series in stats.trends
        ],
        company_breakdown=[
            StatsCompanyTypeResponse(
                label=company_type_label(item.company_type.value),
                count=item.count,
                percent=round(item.count * 100 / stats.company_total),
            )
            for item in stats.company_breakdown
        ],
        company_total=stats.company_total,
        funnel=_to_funnel_response(stats.funnel),
    )


def _has_any_data(stats: ProfileStats) -> bool:
    """У нового пользователя окна пустые — показывать нули как аналитику нечестно."""
    if stats.funnel.total or stats.company_total:
        return True
    return any(point.count for series in stats.trends for point in series.points)


def _to_funnel_response(funnel: FilterFunnel) -> StatsFunnelResponse:
    if funnel.total == 0:
        return StatsFunnelResponse(total=0, rows=[])

    rows = [
        StatsFunnelRowResponse(
            label="Дошло до вас",
            count=funnel.matched,
            percent=round(funnel.matched * 100 / funnel.total),
        )
    ]
    rows.extend(
        StatsFunnelRowResponse(
            label=_REJECTION_LABELS[item.reason],
            count=item.count,
            percent=round(item.count * 100 / funnel.total),
        )
        for item in funnel.rejections
    )
    return StatsFunnelResponse(total=funnel.total, rows=rows)


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


def _level_mode_choice(mode: LevelFilterMode) -> str:
    return mode.value


def _grade_choice(user: User) -> str:
    if user.cv_grade is None:
        return GradeChoice.ANY.value
    return user.cv_grade.value


def _experience_level_choice(user: User) -> str:
    if user.cv_experience_level is None:
        return ExperienceLevelChoice.ANY.value
    return user.cv_experience_level.value


def _grade_filter_from_payload(
    choice: GradeChoice,
    mode: LevelModeChoice,
) -> tuple[Grade | None, LevelFilterMode]:
    if mode == LevelModeChoice.IGNORE or choice == GradeChoice.ANY:
        return None, LevelFilterMode.IGNORE
    return Grade(choice.value), LevelFilterMode(mode.value)


def _experience_filter_from_payload(
    choice: ExperienceLevelChoice,
    mode: LevelModeChoice,
) -> tuple[ExperienceLevel | None, LevelFilterMode]:
    if mode == LevelModeChoice.IGNORE or choice == ExperienceLevelChoice.ANY:
        return None, LevelFilterMode.IGNORE
    return ExperienceLevel(choice.value), LevelFilterMode(mode.value)
