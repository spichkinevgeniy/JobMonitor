<p align="center">
  <a href="https://t.me/JobMonitorIT_BOT">
    <img loading="lazy" alt="JobMonitor" src="docs/img/jobmonitorlogo.png" width="240"/>
  </a>
</p>

<p align="center">
  <a href="https://t.me/JobMonitorIT_BOT">
    <img alt="Open in Telegram" src="https://img.shields.io/badge/Open%20in-Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white"/>
  </a>
</p>

# JobMonitor

JobMonitor is an open source Telegram service for IT vacancy monitoring, AI-assisted parsing, and personalized delivery of relevant job posts.

The project watches selected Telegram channels, detects vacancy posts, extracts structured data, and filters results against a candidate profile so users receive a cleaner and more relevant feed.

**Bot link:** [Open the bot](https://t.me/JobMonitorIT_BOT)

All tracked source channels are listed in [channels_map.json](channels_map.json).
If your channel or technology niche is missing, you can contribute by updating `channels_map.json`. See [docs/CHANNELS.md](docs/CHANNELS.md) for channel grouping and contribution rules.

## Features

- monitor Telegram channels with Telethon;
- detect whether a message is a vacancy;
- parse vacancy content and candidate preferences with AI;
- match vacancies against user profile and filters;
- deliver relevant jobs through a Telegram bot;
- expose a mini-app and observability stack for operations.

## Demo

<p align="center">
  <a href="https://t.me/JobMonitorIT_BOT">
    <img src="docs/img/jobmonitor-demo.gif" alt="JobMonitor demo" width="900"/>
  </a>
</p>

## Tech Stack

- Python 3.12+ with `uv`
- Aiogram, Telethon, FastAPI
- Pydantic, PydanticAI, Google Gemini
- PostgreSQL, SQLAlchemy, Alembic
- Pytest, Ruff, MyPy
- Docker Compose, Prometheus, Grafana, Loggfire

## Quick Start

### Local development

```bash
cp .env.sample .env
uv sync --dev
uv run alembic upgrade head
uv run -m app.main
```

### Docker

```bash
cp .env.sample .env
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
```

Detailed setup instructions are in [docs/INSTALL.md](docs/INSTALL.md).

If you want to run a similar vacancy-monitoring bot for your own needs, this repository is designed to be a practical starting point: you can fork it, configure your own Telegram bot and channel sources, and adapt the filters, prompts, and delivery flow to your use case.

## Development

Useful commands:

```bash
make install
make quality
make lint
make test
make dev-up
make obs-up
```

The tracked Telegram channels are configured in [channels_map.json](channels_map.json).
If the current bot does not cover enough useful Telegram channels, you can help by opening a pull request that adds relevant sources to `channels_map.json`. This is one of the simplest and most high-impact ways to contribute, and these updates are especially welcome.

## Contributing

For guidance on setting up a development environment and how to contribute to JobMonitor, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Reporting a Security Vulnerability

See our [security policy](SECURITY.md).

## Security Notes

Do not commit real `.env` files, Telegram session files, API tokens, or production credentials. Use `.env.sample` as the template for local configuration.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
