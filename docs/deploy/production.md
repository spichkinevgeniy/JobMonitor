# Production Deploy (VPS + Docker)

## Preconditions

- Docker and Docker Compose plugin are installed on the VPS.
- Repository is cloned on the VPS.
- `.env` exists on the server and is not committed to git.
- `MIRROR_CHANNEL` is an integer channel ID.

## Minimal `.env` checklist

- `APP_ENV=production`
- `API_ID`, `API_HASH`, `BOT_TOKEN`
- `GOOGLE_API_KEY`
- `MIRROR_CHANNEL` (int, for example `-1001234567890`)
- `POSTGRES_SERVER=db`
- `POSTGRES_PORT=5432`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `SENTRY_ENV=production`
- `LOGFIRE_ENV=production`
- `METRICS_ENABLED=true`

## First deployment

1. Pull code:
```bash
git pull --ff-only
```

2. Start only database:
```bash
docker compose --env-file .env -f docker-compose.yml up -d db
```

3. Apply migrations:
```bash
make prod-migrate
```

4. Start application:
```bash
docker compose --env-file .env -f docker-compose.yml up -d app
```

5. Check logs:
```bash
make prod-logs SERVICE=app
```

## Telethon first authorization

1. On first start, app may print QR login URL or QR code in logs.
2. Complete authorization once.
3. Restart app:
```bash
docker compose --env-file .env -f docker-compose.yml restart app
```
4. Ensure no re-authorization is required. Session is stored in `telethon_session` volume.

## Regular release

1. Pull updates:
```bash
git pull --ff-only
```
2. Rebuild and restart:
```bash
make prod-up
```
3. Run migrations if schema changed:
```bash
make prod-migrate
```
4. Verify:
```bash
make prod-ps
make prod-logs SERVICE=app
```

## Health checks

- Bot responds to `/start`.
- Scraper receives and processes new channel messages.
- Metrics endpoint is available on `127.0.0.1:8000/metrics`.
- Sentry receives errors when `SENTRY_DSN` is configured.

## Rollback

1. Checkout previous stable commit/tag:
```bash
git checkout <stable_tag_or_commit>
```
2. Rebuild and restart:
```bash
make prod-up
```
3. Review logs:
```bash
make prod-logs SERVICE=app
```

## Backup checklist (local Postgres in Docker)

- Run daily logical backup:
```bash
docker compose --env-file .env -f docker-compose.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > /opt/backups/job_monitor_$(date +%F).sql
```
- Store backups outside Docker volumes.
- Keep at least 7 daily and 4 weekly backups.
