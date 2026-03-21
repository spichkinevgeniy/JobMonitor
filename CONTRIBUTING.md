# Contributing

This guide covers the day-to-day contribution workflow for JobMonitor.

## Contributing In General

Thanks for considering a contribution to JobMonitor.

One of the most helpful ways to contribute is to suggest a relevant Telegram job channel by updating `channels_map.json`.
We especially welcome pull requests like this. If you open one, a maintainer will review the suggested channel and merge it if everything looks good.

Before you start:

- search existing issues and pull requests to avoid duplicate work;
- open an issue first for large changes, architectural work, or behavior changes;
- keep pull requests focused and easy to review;
- update docs when setup, behavior, or public interfaces change;
- never commit real `.env` files, Telegram session files, API tokens, or production data.

Recommended workflow:

1. Fork the repository.
2. Create a feature branch from `main`.
3. Make small, reviewable commits.
4. Run local checks before opening a pull request.
5. Open a pull request with context and verification steps.

Suggested branch names:

- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`

Please include in every pull request:

- a clear summary of what changed;
- why the change is needed;
- how you tested it;
- screenshots if the mini-app UI changed;
- notes about migrations, environment variables, or breaking changes.

## Suggesting Telegram Channels

If you know a good Telegram channel with IT vacancies, a pull request that updates `channels_map.json` is a great contribution.

When proposing a new channel:

- add the channel in `channels_map.json`;
- place it under the closest existing technology bucket;
- mention why it is relevant for JobMonitor users;
- say whether the channel is public or private;
- mention any language, region, or niche focus if that matters.

Classification guidelines for `channels_map.json`:

- put Python channels under `Python`;
- put frontend-oriented channels such as React, Vue, Angular, and similar web UI sources under `JavaScript`;
- put Java and broad JVM backend channels under `JAVA`;
- put Kotlin-specific channels under `KOTLIN`;
- put Go channels under `GO`;
- put .NET channels under `C#`;
- put DevOps and SRE channels under `DEVOPS`;
- put QA channels under `QA`;
- put broad multi-stack channels under `Common`.

If a channel covers several stacks, choose the primary topic. If there is no clear dominant stack, use `Common`.
Please also avoid duplicates and empty entries when editing the file.
More details are documented in [docs/CHANNELS.md](docs/CHANNELS.md).

These pull requests are especially appreciated because they directly improve the quality of the monitored vacancy sources.
A maintainer will check the suggested channel and merge the pull request if it is a good fit.

## Issues

Use GitHub Issues for bugs, feature requests, and scoped design discussions.

Before opening a new issue:

- search the tracker for an existing report or proposal;
- collect reproduction steps, expected behavior, and actual behavior;
- include environment details when they matter, such as OS, Python version, and whether you used local `uv` setup or Docker;
- attach logs, stack traces, screenshots, or sample payloads when they help explain the problem.

For larger changes, opening an issue before implementation helps align the approach and avoid rework.

If you discover a security vulnerability, do not open a public issue. Follow [SECURITY.md](SECURITY.md) instead.

## Developing: Usage of uv

The local Python workflow in this project is built around `uv`.

Requirements:

- Python 3.12 or newer;
- `uv`;
- PostgreSQL if you run the app without Docker.

Install development dependencies:

```bash
uv sync --dev
```

If you want a local virtual environment first:

```bash
uv venv .venv
```

Start the database and apply migrations:

```bash
docker compose up -d db
uv run alembic upgrade head
```

Run the app locally:

```bash
uv run -m app.main
```

Useful commands:

```bash
make install
make run
make run-miniapp
make lint
make test
```

For hook-based local checks:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Full environment setup and Telegram-specific configuration are described in [docs/INSTALL.md](docs/INSTALL.md).

## Coding Style Guidelines

Follow the existing project structure and naming patterns instead of introducing a parallel style.

Current tool-based conventions:

- Ruff line length is `100`;
- Ruff lint rules include `E`, `F`, `I`, `UP`, `B`, `YTT`, `T10`, `T20`, `C4`, `PERF`, and `PIE`;
- MyPy runs in strict mode;
- the project targets Python `3.12`.

Practical expectations:

- keep functions, services, and modules cohesive;
- prefer explicit typing where the codebase already expects it;
- keep changes small and readable;
- update related docs when behavior or setup changes.

Run formatting and static checks before opening a pull request:

```bash
make format
make lint
```

Equivalent direct commands:

```bash
uv run python -m ruff check app tests --fix
uv run python -m ruff format app tests
uv run python -m ruff check app tests
uv run python -m mypy app
```

## Tests

The project uses `pytest`, with tests stored under the `tests/` directory.

Available test markers include:

- `unit`
- `integration`
- `functional`

Run the full suite:

```bash
make test
```

Run narrower suites when needed:

```bash
make test-unit
make test-integration
```

Equivalent direct command:

```bash
uv run -m pytest -q
```

Add or update tests whenever your change affects behavior. If a change is hard to cover with an automated test, explain the gap in the pull request description.
