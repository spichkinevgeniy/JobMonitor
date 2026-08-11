<p align="center">
  <a href="https://t.me/JobMonitorIT_BOT">
    <img loading="lazy" alt="JobMonitor" src="docs/img/logo.png" width="240"/>
  </a>
</p>

<p align="center">
  <a href="https://t.me/JobMonitorIT_BOT">
    <img alt="Открыть в Telegram" src="https://img.shields.io/badge/Open%20in-Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white"/>
  </a>
</p>

# JobMonitor

JobMonitor — сервис с открытым исходным кодом, который ищет IT-вакансии в Telegram. Он следит за выбранными каналами, распознаёт вакансии, извлекает из них данные и сравнивает их с профилем кандидата. Пользователь получает более чистую и подходящую ему ленту.

JobMonitor начинался как учебный проект. Поэтому местами архитектура здесь серьёзнее, чем требует обычный бот. Это сделано отчасти ради практики — и просто потому, что было интересно.

**Бот:** [открыть JobMonitor](https://t.me/JobMonitorIT_BOT)

## Соберём вакансии со всех каналов

<p align="center">
  <a href="docs/CHANNELS.md">
    <img loading="lazy" alt="Добавить Telegram-канал в JobMonitor" src="docs/img/baner.png" width="900"/>
  </a>
</p>

Список отслеживаемых каналов хранится в [channels_map.json](channels_map.json). Если нужного канала или направления нет, добавьте его по [инструкции](docs/CHANNELS.md).

## Возможности

- отслеживание Telegram-каналов через Telethon;
- распознавание сообщений с вакансиями;
- разбор вакансий и предпочтений кандидата с помощью ИИ;
- фильтрация вакансий по профилю пользователя;
- отправка подходящих вакансий через Telegram-бота;
- мини-приложение, метрики и мониторинг.

## Демо

<p align="center">
  <a href="https://t.me/JobMonitorIT_BOT">
    <img src="docs/img/jobmonitor-demo.gif" alt="Демонстрация JobMonitor" width="900"/>
  </a>
</p>

## Технологии

- Python 3.12+ и `uv`;
- Aiogram, Telethon и FastAPI;
- Pydantic, PydanticAI и OpenRouter;
- PostgreSQL, SQLAlchemy и Alembic;
- Pytest, Ruff и MyPy;
- Docker Compose, Prometheus, Grafana и Logfire.

Для небольшого Telegram-бота стек выглядит внушительно. Так и есть. Если вам нужен только простой поиск вакансий, часть компонентов можно убрать — бот не обидится.

## Быстрый запуск

### Локально

```text
copy .env.sample .env
uv sync
cd frontend
npm ci
cd ..
uv run python scripts/dev.py
```

Команда сама поднимает PostgreSQL, ждёт healthcheck, применяет миграции и
запускает FastAPI, Vite, HTTPS-туннель и Telegram-бот без scraper/Telethon.
После первой установки последующие запуски требуют только последней команды.

Для работы только в браузере используйте `uv run python scripts/dev.py --browser`.
Для запуска вместе с Telethon scraper —
`uv run python scripts/dev.py --with-scraper`.

### В Docker

```bash
cp .env.sample .env
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
```

Для production deployment с React shell, Dashboard и Nginx:

```bash
make prod-deploy
```

Nginx становится единой HTTP-точкой входа на `PUBLIC_HTTP_PORT`
(по умолчанию `8080`). Подробности и публичные URL описаны в
[инструкции по установке](docs/INSTALL.md#production-deployment).

Подробная настройка описана в [инструкции по установке](docs/INSTALL.md).

Репозиторий можно использовать как основу для своего бота: сделайте форк, укажите токены и каналы, затем настройте фильтры, промпты и отправку вакансий.

## Разработка

Основная команда локальной разработки Mini App:

```text
uv run python scripts/dev.py
```

Подробности, режимы запуска и требования к HTTPS-туннелю описаны в
[инструкции по установке](docs/INSTALL.md).

О правилах работы с проектом читайте в [руководстве для участников](CONTRIBUTING.md). Самый простой полезный вклад — добавить подходящий канал в `channels_map.json`.

## Безопасность

Не добавляйте в репозиторий файл `.env`, сессии Telegram, токены, ключи API и данные продакшена. Для локальной настройки используйте `.env.sample`.

Об уязвимостях сообщайте по [правилам безопасности](SECURITY.md).

## Лицензия

Проект распространяется по лицензии MIT. Текст лицензии находится в файле [LICENSE](LICENSE).
