# Channel Sources

This document explains how `channels_map.json` is organized and how to add or classify Telegram channels for JobMonitor.

## File Format

Tracked sources are stored in [`channels_map.json`](../channels_map.json) as a mapping from category name to a list of channel references.

The project accepts channel references in these forms:

- `https://t.me/channel_name`
- `@channel_name`
- numeric chat id

Public `https://t.me/...` links are preferred when possible because they are easier to review and maintain.

## Classification Rules

Use the closest existing category and keep the mapping consistent.

- Python-focused channels go to `Python`.
- Frontend-heavy channels such as React, Vue, Angular, or general web frontend usually go to `JavaScript`.
- Java and broad JVM backend channels usually go to `JAVA`.
- Kotlin-specific channels go to `KOTLIN`.
- Go channels go to `GO`.
- .NET channels go to `C#`.
- DevOps and SRE channels go to `DEVOPS`.
- QA-focused channels go to `QA`.
- Broad multi-stack channels that are not tied to one technology go to `Common`.

If a channel covers several stacks, choose the primary topic. If there is no clear dominant stack, use `Common`.

## Editing Guidelines

- Prefer the channel's main topic over occasional posts about other stacks.
- Avoid duplicates and empty entries.
- Keep channel references in a consistent format inside the same category.
- Use public links when available.
- If a channel is private, make sure the Telethon account can join and read it before relying on it in production.

