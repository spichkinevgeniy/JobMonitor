# Installation

This guide covers local development and Docker-based setup for JobMonitor.

## Requirements

- Python 3.12 or newer
- `uv`
- Docker and Docker Compose for containerized setup
- PostgreSQL if you run the app locally without Docker
- Telegram API credentials from `https://my.telegram.org`
- A bot token from `@BotFather`
- An LLM API key for vacancy parsing

## 1. Clone the repository

```bash
git clone https://github.com/Popachka/JobMonitor.git
cd JobMonitor
```

## 2. Create local environment

Create a local config from the sample:

```bash
cp .env.sample .env
```

Required values to review before the first run:

- `API_ID`
- `API_HASH`
- `BOT_TOKEN`
- `MIRROR_CHANNEL`
- `POSTGRES_*`
- `GOOGLE_API_KEY`
- `MINI_APP_BASE_URL` if you use Telegram WebApp buttons

Never commit `.env` with real secrets.

## Telegram setup

JobMonitor uses two different Telegram actors:

- a regular Telegram user account authorized through Telethon;
- a Telegram bot created with `@BotFather`.

They have different responsibilities:

- Telethon listens to source channels from `channels_map.json`;
- Telethon forwards incoming source messages into the mirror channel;
- the bot forwards matched vacancies from the mirror channel to end users.

### 1. Create a Telegram bot

Create a bot via `@BotFather` and place its token into `.env`:

```bash
BOT_TOKEN="123456:your_bot_token"
```

### 2. Get `API_ID` and `API_HASH` for Telethon

Telethon does not use the bot token for channel monitoring. It uses Telegram API credentials of a regular user account.

To get them:

1. Open `https://my.telegram.org`
2. Sign in with the phone number of the Telegram account that will be used by Telethon
3. Open `API Development Tools`
4. Create an application
5. Copy `api_id` and `api_hash` into `.env`

Example:

```bash
API_ID="12345678"
API_HASH="your_api_hash"
```

This same Telegram account is the one that will log in on first launch.

### 3. Choose Telethon login mode

For QR login:

```bash
TELETHON_LOGIN_MODE="qr"
```

For phone login:

```bash
TELETHON_LOGIN_MODE="phone"
TELEGRAM_PHONE="+79990000000"
```

If the Telegram account has 2FA enabled, also set:

```bash
TELEGRAM_2FA_PASSWORD="your_2fa_password"
```

### 4. Create a mirror channel

Create a dedicated Telegram channel that will be used as an internal mirror for all tracked messages.

Why it is needed:

- Telethon forwards every new source message into this channel;
- the bot later forwards matched vacancies from this channel to users.

### 5. Add the required actors to the mirror channel

Add both of these to the mirror channel:

- the Telegram bot created in `@BotFather`;
- the Telegram user account used by Telethon.

The simplest setup is to make both of them channel administrators.

Why:

- the Telethon user must be able to forward messages into the mirror channel;
- the bot must be able to access messages in the mirror channel and forward them to users.

### 6. Get the `MIRROR_CHANNEL` id

`MIRROR_CHANNEL` must be the numeric Telegram chat id of the mirror channel, usually in the form `-100...`.

One practical way to get it:

1. Add your bot to the mirror channel as admin
2. Send a test message into that channel
3. Run:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

4. Find `channel_post.chat.id` in the response
5. Put that value into `.env`

Example:

```bash
MIRROR_CHANNEL="-1001234567890"
```

### 7. Configure source channels for monitoring

Tracked source channels are configured in `channels_map.json`.

The project accepts channel references in these forms:

- `https://t.me/channel_name`
- `@channel_name`
- numeric chat id

Public `https://t.me/...` links are the simplest option and are already used in the repository example.

Important:

- the Telethon user account must have access to the channels you want to monitor;
- for private channels, that account must join them manually before launch;
- the bot itself does not monitor source channels, only Telethon does.

For channel grouping and contribution rules, see [docs/CHANNELS.md](CHANNELS.md).

### 8. First launch behavior

On first start, Telethon will ask you to authorize the Telegram user account:

- in `qr` mode, scan the QR code in Telegram;
- in `phone` mode, confirm the login code sent by Telegram.

After successful login, the session is stored locally and reused on the next launches.

## Option A. Local development with uv

### Install dependencies

```bash
uv sync --dev
```

### Start PostgreSQL

You can use your local PostgreSQL instance or start only the database via Docker:

```bash
docker compose up -d db
```

### Apply migrations

```bash
uv run alembic upgrade head
```

### Run the application

```bash
uv run -m app.main
```

To run only the mini-app server:

```bash
make run-miniapp
```

## Option B. Docker Compose

For a full local stack with app, database, and pgAdmin:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
```

Useful commands:

```bash
make dev-up
make dev-down
make dev-logs SERVICE=app
make dev-ps
```

## Observability stack

To run Prometheus and Grafana locally:

```bash
make obs-up
```

Stop it with:

```bash
make obs-down
```

## Quality checks

Run linters and tests before opening a pull request:

```bash
make lint
make test
```

## Troubleshooting

### Telegram session or login issues

- remove local session artifacts if you want to re-authenticate;
- confirm `API_ID`, `API_HASH`, and phone number are correct;
- if 2FA is enabled, set `TELEGRAM_2FA_PASSWORD`.

### Database connection issues

- make sure PostgreSQL is running;
- verify `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`;
- run migrations after the database becomes available.

### Mini-app URL issues

- Telegram WebApp requires a public HTTPS URL;
- set `MINI_APP_BASE_URL` to a reachable HTTPS endpoint such as a tunnel or deployed domain.
