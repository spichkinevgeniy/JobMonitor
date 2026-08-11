"""Доступ к собранному сервису наблюдаемости из мест вне графа зависимостей.

Мини-апп поднимается uvicorn'ом по строковому пути, а роутеры бота — это
модульные объекты. Ни туда, ни туда экземпляр из bootstrap не передать, а
заводить второй нельзя: у него будет своё хранилище счётчиков.
"""

from app.application.ports.observability_port import (
    Feature,
    IObservabilityService,
)

_service: IObservabilityService | None = None


def set_observability_service(service: IObservabilityService) -> None:
    global _service
    _service = service


def observe_feature(feature: Feature, count: int = 1) -> None:
    """Тихо ничего не делает, пока сервис не собран — например, в тестах."""
    if _service is not None:
        _service.observe_feature_used(feature, count)
