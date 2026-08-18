# JobMonitor

JobMonitor is a vacancy-monitoring platform built around a Telegram bot and
Telegram Mini Apps. The repository contains a FastAPI backend, PostgreSQL,
React and TypeScript frontends, and an Nginx production gateway.

This file is the entry point for AI agents working in the repository. Read it
before modifying code. When a more specific `AGENTS.md` exists closer to the
code being changed, follow both files; the nearest file provides the more
specific instructions.

## General Guidelines

- Do not modify code unrelated to the current task.
- Inspect existing code and conventions before introducing a new pattern.
- Prefer clear, maintainable code over unnecessary abstractions.
- Use meaningful names that reflect the domain.
- Do not add comments that merely repeat what the code already expresses.
- Do not introduce a dependency or architectural layer without a concrete
  requirement.
- Preserve backwards compatibility unless the task explicitly requires a
  breaking change.
- Do not edit generated files or build output manually.

## Architecture

```text
JobMonitor/
├── app/                         # Telegram bot and FastAPI backend
├── frontend/                    # React and TypeScript Mini Apps
│   ├── apps/
│   │   ├── shell/               # Onboarding and search profile settings
│   │   └── dashboard/           # Search status and vacancies
│   └── packages/                # Shared frontend packages
└── nginx/                       # Production frontend gateway