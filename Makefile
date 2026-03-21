IMAGE_NAME = job_monitor
PYTHON_MAIN = app.main
PROJECT_DIR = app
TEST_DIR = tests
VENV_DIR = .venv
LOGFIRE_PROJECT = jobmonitor
DEV_COMPOSE = docker-compose -f docker-compose.yml -f docker-compose.override.yml
PROD_COMPOSE = docker-compose -f docker-compose.yml
OBS_COMPOSE = docker-compose -f docker-compose.observability.yml
BACKUP_DIR ?= /opt/backups

.PHONY: help venv install run run-miniapp quality lint format test test-unit test-integration clean \
	docker-build \
	dev-up dev-down dev-destroy dev-logs dev-ps dev-restart \
	prod-up prod-down prod-destroy prod-logs prod-ps prod-restart prod-migrate \
	prod-db-up prod-app-up prod-backup prod-deploy \
	precommit-install precommit-run \
	obs-up obs-down obs-destroy obs-logs obs-ps \
	dev-up-all dev-down-all dev-destroy-all \
	prod-up-all prod-down-all prod-destroy-all \
	docker-up docker-down docker-logs \
	logfire-auth logfire-use-project

default: help

help:
	@echo "Available make commands:"
	@echo "  venv              - Create a virtual environment (uv)"
	@echo "  install           - Install project dependencies (uv sync)"
	@echo "  run               - Run the app locally (bot + scraper + mini-app)"
	@echo "  run-miniapp       - Run only the mini-app server locally"
	@echo "  quality           - Run CI gate (ruff + format check + tests)"
	@echo "  lint              - Run ruff checks + format check + mypy"
	@echo "  format            - Auto-fix with ruff and apply formatting"
	@echo "  test              - Run all tests"
	@echo "  test-unit         - Run unit tests"
	@echo "  test-integration  - Run integration tests"
	@echo "  precommit-install - Install pre-commit hooks"
	@echo "  precommit-run     - Run pre-commit hooks for all files"
	@echo "  clean             - Delete temporary files and caches"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build      - Build app image"
	@echo "  dev-up            - Start dev stack (app + db + pgadmin), build if needed"
	@echo "  dev-down          - Stop dev stack (keep volumes)"
	@echo "  dev-destroy       - Stop dev stack and remove volumes/orphans"
	@echo "  dev-ps            - Show dev services status"
	@echo "  dev-logs          - Follow dev logs (use SERVICE=app|db|pgadmin)"
	@echo "  dev-restart       - Restart dev stack"
	@echo "  prod-up           - Recreate prod stack (down + up --build)"
	@echo "  prod-down         - Stop prod stack (keep volumes)"
	@echo "  prod-destroy      - Stop prod stack and remove volumes/orphans"
	@echo "  prod-ps           - Show prod services status"
	@echo "  prod-logs         - Follow prod logs (use SERVICE=app|db)"
	@echo "  prod-restart      - Restart prod stack"
	@echo "  prod-migrate      - Run Alembic migrations in prod stack"
	@echo "  prod-db-up        - Start only postgres in prod stack"
	@echo "  prod-app-up       - Start only app in prod stack"
	@echo "  prod-backup       - Dump prod postgres to $(BACKUP_DIR)"
	@echo "  prod-deploy       - Full prod deploy (up + migrate + ps)"
	@echo ""
	@echo "Observability:"
	@echo "  obs-up            - Start Prometheus + Grafana"
	@echo "  obs-down          - Stop observability stack (keep volumes)"
	@echo "  obs-destroy       - Stop observability stack and remove volumes/orphans"
	@echo "  obs-ps            - Show observability services status"
	@echo "  obs-logs          - Follow observability logs (use SERVICE=prometheus|grafana)"
	@echo ""
	@echo "Combined:"
	@echo "  dev-up-all        - Start dev stack + observability"
	@echo "  dev-down-all      - Stop dev stack + observability"
	@echo "  dev-destroy-all   - Destroy dev stack + observability (with volumes)"
	@echo "  prod-up-all       - Start prod stack + observability"
	@echo "  prod-down-all     - Stop prod stack + observability"
	@echo "  prod-destroy-all  - Destroy prod stack + observability (with volumes)"
	@echo ""
	@echo "Legacy aliases:"
	@echo "  docker-up         - Alias for dev-up"
	@echo "  docker-down       - Alias for dev-down"
	@echo "  docker-logs       - Alias for dev-logs"
	@echo ""
	@echo "  logfire-auth      - Authenticate Logfire locally"
	@echo "  logfire-use-project - Select Logfire project ($(LOGFIRE_PROJECT))"

venv:
	uv venv $(VENV_DIR)

install:
	uv sync

run:
	uv run -m $(PYTHON_MAIN)

quality:
	@echo "Starting quality gate..."
	uv run python -m ruff check $(PROJECT_DIR) $(TEST_DIR)
	uv run python -m ruff format --check $(PROJECT_DIR) $(TEST_DIR)
	uv run -m pytest -q
	@echo "Quality gate completed!"

lint:
	@echo "Starting checks..."
	uv run python -m ruff check $(PROJECT_DIR) $(TEST_DIR)
	uv run python -m ruff format --check $(PROJECT_DIR) $(TEST_DIR)
	uv run python -m mypy $(PROJECT_DIR)
	@echo "Checks completed!"

format:
	uv run python -m ruff check $(PROJECT_DIR) $(TEST_DIR) --fix
	uv run python -m ruff format $(PROJECT_DIR) $(TEST_DIR)

test:
	uv run -m pytest -q

test-unit:
	uv run -m pytest $(TEST_DIR)/unit -q

test-integration:
	uv run -m pytest $(TEST_DIR)/integration -q

precommit-install:
	uv run pre-commit install

precommit-run:
	uv run pre-commit run --all-files

clean:
	@echo "Start cleaning..."
	uv run python -c "from pathlib import Path; import shutil; root = Path('.'); [p.unlink() for p in root.rglob('*.pyc')]; [p.unlink() for p in root.rglob('*.pyo')]; [shutil.rmtree(p, ignore_errors=True) for p in root.rglob('__pycache__') if p.is_dir()]; [shutil.rmtree(p, ignore_errors=True) for p in (root / '.mypy_cache', root / '.ruff_cache', root / '.pytest_cache')]; [shutil.rmtree(p, ignore_errors=True) for p in root.glob('*.egg-info') if p.is_dir()]"
	@echo "Cleaning done!"

docker-build:
	docker build -t $(IMAGE_NAME) .

dev-up:
	$(DEV_COMPOSE) up -d --build

dev-down:
	$(DEV_COMPOSE) down

dev-destroy:
	$(DEV_COMPOSE) down -v --remove-orphans

dev-logs:
	$(DEV_COMPOSE) logs -f $(SERVICE)

dev-ps:
	$(DEV_COMPOSE) ps

dev-restart:
	$(DEV_COMPOSE) restart

prod-up:
	$(PROD_COMPOSE) down --remove-orphans
	$(PROD_COMPOSE) up -d --build

prod-down:
	$(PROD_COMPOSE) down

prod-destroy:
	$(PROD_COMPOSE) down -v --remove-orphans

prod-logs:
	$(PROD_COMPOSE) logs -f $(SERVICE)

prod-ps:
	$(PROD_COMPOSE) ps

prod-restart:
	$(PROD_COMPOSE) restart

prod-migrate:
	$(PROD_COMPOSE) run --rm app uv run alembic upgrade head

prod-db-up:
	$(PROD_COMPOSE) up -d db

prod-app-up:
	$(PROD_COMPOSE) up -d app

prod-backup:
	mkdir -p $(BACKUP_DIR)
	$(PROD_COMPOSE) exec -T db sh -lc 'pg_dump -U "$$POSTGRES_USER" "$$POSTGRES_DB"' > $(BACKUP_DIR)/job_monitor_$$(date +%F).sql

prod-deploy:
	$(MAKE) prod-up
	$(MAKE) prod-migrate
	$(MAKE) prod-ps

obs-up:
	$(OBS_COMPOSE) up -d

obs-down:
	$(OBS_COMPOSE) down

obs-destroy:
	$(OBS_COMPOSE) down -v --remove-orphans

obs-logs:
	$(OBS_COMPOSE) logs -f $(SERVICE)

obs-ps:
	$(OBS_COMPOSE) ps

dev-up-all: dev-up obs-up

dev-down-all: dev-down obs-down

dev-destroy-all: dev-destroy obs-destroy

prod-up-all: prod-up obs-up

prod-down-all: prod-down obs-down

prod-destroy-all: prod-destroy obs-destroy

docker-up: dev-up

docker-down: dev-down

docker-logs: dev-logs

logfire-auth:
	uv run logfire auth

logfire-use-project:
	uv run logfire projects use $(LOGFIRE_PROJECT)
