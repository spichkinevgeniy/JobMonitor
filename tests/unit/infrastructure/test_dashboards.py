"""Панели дашбордов ссылаются только на существующие метрики.

Опечатка в имени не ломает ничего заметно — панель просто всегда пустая,
и это обнаруживается спустя недели.
"""

import json
import re
from pathlib import Path

import pytest
from prometheus_client import REGISTRY

import app.infrastructure.observability.metrics  # noqa: F401  (регистрирует метрики)

DASHBOARDS = sorted(Path("grafana/dashboards").glob("*.json"))
METRIC_NAME = re.compile(r"\bjob_monitor_[a-z_]+\b")


def _known_metrics() -> set[str]:
    names = set()
    for metric in REGISTRY.collect():
        names.add(metric.name)
        for sample in metric.samples:
            names.add(sample.name)
    return names


def _expressions(path: Path) -> list[str]:
    dashboard = json.loads(path.read_text(encoding="utf-8"))
    return [
        target["expr"]
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
        if "expr" in target
    ]


@pytest.mark.parametrize("path", DASHBOARDS, ids=lambda p: p.name)
def test_dashboard_references_existing_metrics(path: Path) -> None:
    known = _known_metrics()
    used = {name for expr in _expressions(path) for name in METRIC_NAME.findall(expr)}

    unknown = {
        name for name in used if name not in known and name.removesuffix("_total") not in known
    }
    assert not unknown, f"{path.name}: метрик не существует — {sorted(unknown)}"


@pytest.mark.parametrize("path", DASHBOARDS, ids=lambda p: p.name)
def test_panel_ids_are_unique(path: Path) -> None:
    dashboard = json.loads(path.read_text(encoding="utf-8"))
    ids = [panel["id"] for panel in dashboard["panels"]]

    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("path", DASHBOARDS, ids=lambda p: p.name)
def test_uid_is_unique_across_dashboards(path: Path) -> None:
    """Совпадение uid — и Grafana молча покажет один дашборд вместо двух."""
    uids = [json.loads(other.read_text(encoding="utf-8"))["uid"] for other in DASHBOARDS]

    assert len(uids) == len(set(uids))


@pytest.mark.parametrize("path", DASHBOARDS, ids=lambda p: p.name)
def test_gauges_are_not_wrapped_in_increase(path: Path) -> None:
    """increase на gauge даёт мусор: значение восстанавливается из БД, а не растёт монотонно."""
    gauge_names = (
        "job_monitor_feature_used",
        "job_monitor_messages_skipped",
        "job_monitor_match_rejected",
        "job_monitor_dispatched_by",
    )

    for expr in _expressions(path):
        if "increase(" not in expr:
            continue
        inner = expr[expr.index("increase(") :]
        assert not any(name in inner for name in gauge_names), (
            f"{path.name}: increase на gauge — {expr}"
        )
