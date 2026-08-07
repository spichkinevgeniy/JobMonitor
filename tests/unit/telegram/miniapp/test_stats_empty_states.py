"""Пустые состояния аналитики: у нового пользователя показывать нечего."""

from datetime import date

from app.application.services.stats_service import (
    CompanyTypeCount,
    FilterFunnel,
    ProfileStats,
    TrendGranularity,
    TrendPoint,
    TrendSeries,
)
from app.domain.shared.value_objects import CompanyType
from app.telegram.miniapp.routes import _has_any_data

BUCKET = date(2026, 8, 1)


def _stats(
    trend_counts: list[int] | None = None,
    company_total: int = 0,
    funnel_total: int = 0,
) -> ProfileStats:
    return ProfileStats(
        trends=[
            TrendSeries(
                granularity=TrendGranularity.WEEK,
                points=[TrendPoint(bucket_start=BUCKET, count=item) for item in trend_counts or []],
            )
        ],
        company_breakdown=(
            [CompanyTypeCount(company_type=CompanyType.PRODUCT, count=company_total)]
            if company_total
            else []
        ),
        company_total=company_total,
        funnel=FilterFunnel(total=funnel_total, matched=funnel_total, rejections=[]),
    )


def test_fresh_user_has_no_data() -> None:
    assert _has_any_data(_stats(trend_counts=[0, 0, 0])) is False


def test_empty_trend_series_is_not_data() -> None:
    assert _has_any_data(_stats()) is False


def test_trend_with_any_count_is_data() -> None:
    assert _has_any_data(_stats(trend_counts=[0, 0, 1])) is True


def test_company_breakdown_alone_is_data() -> None:
    assert _has_any_data(_stats(trend_counts=[0], company_total=4)) is True


def test_funnel_alone_is_data() -> None:
    """Вакансии могли прийти и все отсеяться фильтрами — это тоже статистика."""
    assert _has_any_data(_stats(trend_counts=[0], funnel_total=7)) is True
