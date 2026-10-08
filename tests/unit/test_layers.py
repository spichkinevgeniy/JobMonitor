"""Зависимости идут внутрь, к домену: нижний слой не знает о верхнем.

Иначе правка кнопки бота тянет за собой инфраструктуру, а домен — базу.
"""

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "app"

# Что может импортировать каждый слой. core — общие мелочи: логгер, настройки.
# bootstrap собирает приложение целиком, ему можно всё, он не проверяется.
ALLOWED = {
    "core": set(),
    "domain": {"core"},
    "application": {"domain", "core"},
    "infrastructure": {"application", "domain", "core"},
    # Долг: Telegram-слой пока ходит в инфраструктуру напрямую.
    "telegram": {"application", "domain", "core", "infrastructure"},
}


def _imported_modules(path: Path) -> set[str]:
    modules = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def _imported_layers(path: Path) -> set[str]:
    layers = set()
    for module in _imported_modules(path):
        parts = module.split(".")
        if parts[0] == "app" and len(parts) > 1:
            layers.add(parts[1])
    return layers


@pytest.mark.parametrize("layer", sorted(ALLOWED))
def test_layer_imports_only_allowed_layers(layer: str) -> None:
    violations = [
        f"{path.relative_to(APP.parent).as_posix()} -> {other}"
        for path in sorted((APP / layer).rglob("*.py"))
        for other in sorted(_imported_layers(path) - ALLOWED[layer] - {layer})
    ]
    assert violations == []


def test_bot_does_not_open_the_database() -> None:
    """Сервисы боту даёт bootstrap — сам он в базу не ходит."""
    offenders = [
        path.relative_to(APP.parent).as_posix()
        for path in sorted((APP / "telegram" / "bot").rglob("*.py"))
        if any(
            module.startswith(("app.infrastructure.db", "sqlalchemy"))
            for module in _imported_modules(path)
        )
    ]
    assert offenders == []
