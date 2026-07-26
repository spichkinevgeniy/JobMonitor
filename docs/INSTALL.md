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

Установите зависимости:

```bash
uv sync --dev
```

Запустите PostgreSQL локально или поднимите только базу в Docker:

```bash
docker compose up -d db
```

Примените миграции и запустите приложение:

```bash
uv run alembic upgrade head
uv run -m app.main
```

Только мини-приложение:

```bash
make run-miniapp
```

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
