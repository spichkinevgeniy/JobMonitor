FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini channels_map.json ./
RUN mkdir -p /app/data

# Пакеты ставятся при сборке. Без --no-sync uv run на каждом старте докачивал
# dev-группу (mypy, ruff, pytest): ~30 МБ и лишние секунды простоя.
CMD ["uv", "run", "--no-sync", "-m", "app.main"]
