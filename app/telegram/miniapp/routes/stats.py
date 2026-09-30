"""Статистика профиля: страница и данные для неё."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.application.dto.miniapp import (
    ProfileStatsResponse,
    SkillSuggestionResponse,
    StatsCompanyTypeResponse,
    StatsExportResponse,
    StatsFunnelResponse,
    StatsFunnelRowResponse,
    StatsTrendPointResponse,
    StatsTrendSeriesResponse,
)
from app.application.ports.observability_port import Feature
from app.application.services.export_service import ExportService
from app.application.services.stats_service import (
    FilterFunnel,
    ProfileStats,
    StatsService,
    TrendGranularity,
    TrendPoint,
)
from app.domain.matching.entities import MatchRejectionReason
from app.domain.user.entities import User
from app.infrastructure.observability import observe_feature
from app.telegram.bot.keyboards import PULSE_SOURCE
from app.telegram.miniapp.deps import get_current_user, get_export_service, get_stats_service
from app.telegram.miniapp.page_context import build_stats_page_context, company_type_label
from app.telegram.miniapp.ui import templates

router = APIRouter()


@router.get("/miniapp/stats", response_class=HTMLResponse, name="miniapp-stats")
async def stats_page(request: Request) -> HTMLResponse:
    if request.query_params.get("source") == PULSE_SOURCE:
        observe_feature(Feature.PULSE_OPEN)
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
    observe_feature(Feature.STATS_OPEN)
    stats = await service.build_profile_stats(user)
    export_count = await export_service.count_available(user.tg_id.value)
    if stats.skill_suggestions:
        observe_feature(Feature.ADVICE_SHOWN)
    return _to_stats_response(user, stats, export_count)


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


_TREND_LAST_LABELS = {
    TrendGranularity.WEEK: "эта неделя",
    TrendGranularity.DAY: "сегодня",
}


def _trend_point_label(point: TrendPoint, granularity: TrendGranularity, *, is_last: bool) -> str:
    """Подпись корзины — дата её начала, но у последней это сбивает с толку.

    Последняя корзина идёт от «сейчас минус окно» до «сейчас», то есть 10.08
    она подписана 03.08 — и выглядит как данные недельной давности, хотя
    включает сегодняшний день.
    """
    if is_last:
        return _TREND_LAST_LABELS[granularity]
    return point.bucket_start.strftime("%d.%m")


def _to_stats_response(
    user: User,
    stats: ProfileStats,
    export_count: int,
) -> ProfileStatsResponse:
    return ProfileStatsResponse(
        has_profile=bool(user.cv_specializations.items and user.cv_skills.items),
        has_data=_has_any_data(stats),
        skill_suggestions=[
            SkillSuggestionResponse(skill=item.skill, unlocks=item.unlocks)
            for item in stats.skill_suggestions
        ],
        export=StatsExportResponse(
            count=export_count,
        ),
        trends=[
            StatsTrendSeriesResponse(
                granularity=series.granularity.value,
                toggle_label=_TREND_TOGGLE_LABELS[series.granularity],
                headline_label=_TREND_HEADLINE_LABELS[series.granularity],
                points=[
                    StatsTrendPointResponse(
                        label=_trend_point_label(
                            point,
                            series.granularity,
                            is_last=index == len(series.points) - 1,
                        ),
                        count=point.count,
                    )
                    for index, point in enumerate(series.points)
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
    # Считаем от всего, что было по специализации, а не от прошедшего
    # префильтр: раньше потеря на навыках не попадала в воронку вообще, и
    # человек с одним навыком видел «отсеяно ноль» вместо реальных потерь.
    total = funnel.specialization_total
    if total == 0:
        return StatsFunnelResponse(total=0, matched=0, rows=[])

    rows = [
        StatsFunnelRowResponse(
            kind="matched",
            label="Дошло до вас",
            count=funnel.matched,
            percent=round(funnel.matched * 100 / total),
        )
    ]
    if funnel.skills_mismatch:
        rows.append(
            StatsFunnelRowResponse(
                kind="skills",
                label="Не совпали навыки",
                count=funnel.skills_mismatch,
                percent=round(funnel.skills_mismatch * 100 / total),
            )
        )
    rows.extend(
        StatsFunnelRowResponse(
            label=_REJECTION_LABELS[item.reason],
            count=item.count,
            percent=round(item.count * 100 / total),
        )
        for item in funnel.rejections
    )
    return StatsFunnelResponse(total=total, matched=funnel.matched, rows=rows)
