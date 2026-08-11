# Установка

JobMonitor можно запустить локально или в Docker.

## Что понадобится

- Python 3.12+;
- `uv`;
- Docker и Docker Compose для запуска в контейнерах;
- PostgreSQL для локального запуска без Docker;
- данные Telegram API с [my.telegram.org](https://my.telegram.org);
- токен бота от `@BotFather`;
- ключ API для языковой модели.

## Подготовка проекта

```bash
git clone https://github.com/spichkinevgeniy/JobMonitor.git
cd JobMonitor
cp .env.sample .env
```

Перед первым запуском заполните в `.env`:

- `API_ID` и `API_HASH`;
- `BOT_TOKEN`;
- `MIRROR_CHANNEL`;
- переменные `POSTGRES_*`;
- `OPENROUTER_API_KEY`;
- `MINI_APP_BASE_URL`, если используете кнопки Telegram WebApp.

Не добавляйте `.env` с настоящими секретами в Git.

## Настройка Telegram

В JobMonitor работают два участника:

- обычный аккаунт Telegram через Telethon читает исходные каналы и пересылает сообщения в канал-зеркало;
- бот читает канал-зеркало и отправляет подходящие вакансии пользователям.

### 1. Создайте бота

Создайте бота через `@BotFather` и добавьте токен в `.env`:

```bash
BOT_TOKEN="123456:your_bot_token"
```

### 2. Получите данные для Telethon

1. Откройте [my.telegram.org](https://my.telegram.org).
2. Войдите по номеру аккаунта, который будет читать каналы.
3. Откройте `API Development Tools`.
4. Создайте приложение.
5. Скопируйте `api_id` и `api_hash` в `.env`.

```bash
API_ID="12345678"
API_HASH="your_api_hash"
```

### 3. Выберите способ входа

По QR-коду:

```bash
TELETHON_LOGIN_MODE="qr"
```

По номеру телефона:

```bash
TELETHON_LOGIN_MODE="phone"
TELEGRAM_PHONE="+79990000000"
```

Если включена двухфакторная защита:

```bash
TELEGRAM_2FA_PASSWORD="your_2fa_password"
```

При первом запуске подтвердите вход. Telethon сохранит локальную сессию и использует её при следующих запусках.

### 4. Создайте канал-зеркало

Создайте отдельный Telegram-канал. Telethon будет пересылать туда найденные сообщения, а бот — забирать подходящие вакансии.

Добавьте в канал бота и аккаунт Telethon. Проще всего назначить обоих администраторами: аккаунту нужен доступ на отправку сообщений, а боту — на чтение и пересылку.

### 5. Узнайте ID канала-зеркала

`MIRROR_CHANNEL` — числовой ID вида `-100...`.

1. Добавьте бота в канал как администратора.
2. Отправьте в канал тестовое сообщение.
3. Выполните:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

4. Найдите `channel_post.chat.id` и запишите значение в `.env`:

```bash
MIRROR_CHANNEL="-1001234567890"
```

### 6. Укажите каналы с вакансиями

Список хранится в `channels_map.json`. Поддерживаются:

- `https://t.me/channel_name`;
- `@channel_name`;
- числовой ID чата.

Для публичных каналов удобнее ссылки `https://t.me/...`. Аккаунт Telethon должен видеть каждый канал. В приватные каналы нужно заранее вступить вручную. Бот исходные каналы не читает.

Категории и правила описаны в [CHANNELS.md](CHANNELS.md).

## Локальный запуск

Для первого запуска установите backend и frontend зависимости:

```text
uv sync
cd frontend
npm ci
cd ..
```

Установите `cloudflared` один раз и убедитесь, что команда доступна через
`PATH`. В Windows это можно сделать через Winget:

```powershell
winget install --id Cloudflare.cloudflared
```

Если executable хранится вне `PATH`, перед запуском можно задать
`JOBMONITOR_CLOUDFLARED` с полным путём к нему. Runner также распознаёт
`%TEMP%\jobmonitor-cloudflared.exe`, использовавшийся в предыдущем локальном
workflow.

Полный Mini App dev-режим запускается из корня одной командой:

```text
uv run python scripts/dev.py
```

Runner последовательно:

1. запускает `docker compose up -d db`;
2. ждёт реальный Docker healthcheck PostgreSQL;
3. выполняет `alembic upgrade head`;
4. запускает FastAPI на `127.0.0.1:8081`;
5. запускает onboarding Vite на `127.0.0.1:5173`;
6. запускает Dashboard Vite на `127.0.0.1:5174`;
7. создаёт HTTPS quick tunnel к onboarding Vite, который проксирует Dashboard;
8. передаёт origin туннеля bot-процессу через `MINI_APP_BASE_URL`;
9. запускает Telegram bot без Telethon scraper.

Vite проксирует относительные `/miniapp/api/*` запросы в FastAPI. Поэтому
обе страницы и API доступны через один публичный origin, а tunnel URL не нужно
копировать в `.env` или исходный код.

Режим без Telegram и туннеля:

```text
uv run python scripts/dev.py --browser
```

Он запускает только БД, миграции, FastAPI и Vite. Локальная страница:
<http://127.0.0.1:5173/miniapp/react/>.
Dashboard доступен по адресу
<http://127.0.0.1:5174/miniapp/dashboard/>.

Режим с Telethon scraper:

```text
uv run python scripts/dev.py --with-scraper
```

Для него дополнительно нужны корректные `API_ID`, `API_HASH`, данные входа
Telethon и `OPENROUTER_API_KEY`.

`Ctrl+C` останавливает backend, frontend, tunnel и bot/scraper. Контейнер БД и
Docker volume не удаляются.

### Повторная проверка регистрации и onboarding

В локальном `APP_ENV="development"` можно разрешить destructive dev-команды
только своим Telegram-аккаунтам. Укажите числовые ID через запятую:

```text
DEV_TELEGRAM_USER_IDS="123456789"
```

- `/dev_reset_me` очищает профиль и onboarding, но сохраняет запись пользователя;
  в ответе появляется WebApp-кнопка для открытия текущего React onboarding;
- `/dev_delete_me` транзакционно удаляет пользователя и связанные локальные данные.
  Следующий `/start` заново проходит обычный `get_or_create` flow и для
  allowlisted dev-пользователя присылает кнопку React onboarding.

После завершения onboarding Mini App автоматически открывает Dashboard с
сохранённым профилем. Повторный `/start` для завершившего onboarding
allowlisted dev-пользователя присылает кнопку `Open Dashboard`.

ID берётся из Telegram update; аргументы команд не принимаются. В production
router этих команд не подключается, а сами команды не регистрируются в меню бота.

## Запуск в Docker Compose

Приложение, база и pgAdmin:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
```

Полезные команды:

```bash
make dev-up
make dev-down
make dev-logs SERVICE=app
make dev-ps
```

## Метрики и графики

Запуск Prometheus и Grafana:

```bash
make obs-up
```

В production порты мониторинга доступны только на самом сервере. Для доступа с
локального компьютера откройте SSH-туннель и не закрывайте терминал, пока
пользуетесь панелями:

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 jobmonitor
```

- Grafana: <http://localhost:3000>
- Prometheus: <http://localhost:9090>

Остановка:

```bash
make obs-down
```

## Проверки

```bash
make quality
```

## Частые проблемы

### Не работает вход в Telegram

- проверьте `API_ID`, `API_HASH` и номер телефона;
- укажите `TELEGRAM_2FA_PASSWORD`, если включена двухфакторная защита;
- удалите локальный файл сессии, если хотите войти заново.

### Нет подключения к базе

- проверьте, что PostgreSQL запущен;
- проверьте `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` и `POSTGRES_PASSWORD`;
- примените миграции после запуска базы.

### Не открывается мини-приложение

Telegram WebApp требует публичный HTTPS-адрес. Укажите доступный адрес в `MINI_APP_BASE_URL`, например адрес туннеля или развёрнутого приложения.
