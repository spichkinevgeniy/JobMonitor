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
from app.telegram.miniapp.routes import _has_any_data, _to_funnel_response

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
        funnel=FilterFunnel(
            total=funnel_total,
            matched=funnel_total,
            rejections=[],
            specialization_total=funnel_total,
            skills_mismatch=0,
        ),
        skill_suggestions=[],
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


class TestFunnelRowKinds:
    """Цвет строки задаётся её видом, а не позицией в списке."""

    def _rows(self, **kwargs: int) -> list:
        stats = _stats(**kwargs)  # type: ignore[arg-type]
        return _to_funnel_response(stats.funnel).rows

    def test_matched_row_is_marked(self) -> None:
        rows = self._rows(trend_counts=[1], funnel_total=5)

        assert rows[0].kind == "matched"

    def test_skills_row_is_its_own_kind(self) -> None:
        funnel = FilterFunnel(
            total=5,
            matched=5,
            rejections=[],
            specialization_total=12,
            skills_mismatch=7,
        )
        rows = _to_funnel_response(funnel).rows

        assert [row.kind for row in rows] == ["matched", "skills"]

    def test_skills_row_absent_without_loss(self) -> None:
        funnel = FilterFunnel(
            total=5, matched=5, rejections=[], specialization_total=5, skills_mismatch=0
        )

        assert all(row.kind != "skills" for row in _to_funnel_response(funnel).rows)
