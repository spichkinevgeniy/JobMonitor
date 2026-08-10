"""Подписи корзин тренда.

Последняя корзина идёт от «сейчас минус окно» до «сейчас»: 10 августа она
подписана датой 03.08 и выглядит как данные недельной давности, хотя
включает сегодняшний день.
"""

from datetime import date

from app.application.services.stats_service import TrendGranularity, TrendPoint
from app.telegram.miniapp.routes import _trend_point_label

POINT = TrendPoint(bucket_start=date(2026, 8, 3), count=40)


class TestLastBucket:
    def test_week_says_this_week(self) -> None:
        label = _trend_point_label(POINT, TrendGranularity.WEEK, is_last=True)

        assert label == "эта неделя"

    def test_day_says_today(self) -> None:
        label = _trend_point_label(POINT, TrendGranularity.DAY, is_last=True)

        assert label == "сегодня"


class TestOtherBuckets:
    def test_week_keeps_start_date(self) -> None:
        assert _trend_point_label(POINT, TrendGranularity.WEEK, is_last=False) == "03.08"

    def test_day_keeps_start_date(self) -> None:
        assert _trend_point_label(POINT, TrendGranularity.DAY, is_last=False) == "03.08"
