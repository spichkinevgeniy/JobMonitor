from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import logfire
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.logger import get_app_logger
from app.telegram.miniapp.deps import get_resume_import_service
from app.telegram.miniapp.onboarding_routes import router as onboarding_router
from app.telegram.miniapp.resume_import_routes import router as resume_import_router
from app.telegram.miniapp.routes import router
from app.telegram.miniapp.search_profile_routes import router as search_profile_router
from app.telegram.miniapp.ui import STATIC_DIR

logger = get_app_logger(__name__)

SHELL_DIST_DIR = Path(__file__).resolve().parents[3] / "frontend" / "apps" / "shell" / "dist"
DASHBOARD_DIST_DIR = (
    Path(__file__).resolve().parents[3] / "frontend" / "apps" / "dashboard" / "dist"
)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Задачи разбора живут в процессе: всё, что осталось «в работе»
    # с прошлого запуска, выполнять уже некому.
    try:
        orphaned = await get_resume_import_service().fail_orphaned()
        if orphaned:
            logger.warning("Failed %s resume import jobs left by a restart", orphaned)
    except Exception:
        logger.exception("Failed to sweep interrupted resume imports")
    yield


def build_miniapp_app() -> FastAPI:
    miniapp = FastAPI(title="JobMonitor Mini App", lifespan=_lifespan)
    logfire.instrument_fastapi(miniapp)
    miniapp.mount("/miniapp/static", StaticFiles(directory=str(STATIC_DIR)), name="miniapp-static")
    if SHELL_DIST_DIR.is_dir():
        miniapp.mount(
            "/miniapp/react",
            StaticFiles(directory=str(SHELL_DIST_DIR), html=True),
            name="miniapp-react",
        )
    if DASHBOARD_DIST_DIR.is_dir():
        miniapp.mount(
            "/miniapp/dashboard",
            StaticFiles(directory=str(DASHBOARD_DIST_DIR), html=True),
            name="miniapp-dashboard",
        )
    miniapp.include_router(router)
    miniapp.include_router(onboarding_router)
    miniapp.include_router(resume_import_router)
    miniapp.include_router(search_profile_router)
    return miniapp


app = build_miniapp_app()
