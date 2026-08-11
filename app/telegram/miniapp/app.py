from pathlib import Path

import logfire
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.telegram.miniapp.onboarding_routes import router as onboarding_router
from app.telegram.miniapp.routes import router
from app.telegram.miniapp.search_profile_routes import router as search_profile_router
from app.telegram.miniapp.ui import STATIC_DIR

SHELL_DIST_DIR = Path(__file__).resolve().parents[3] / "frontend" / "apps" / "shell" / "dist"
DASHBOARD_DIST_DIR = (
    Path(__file__).resolve().parents[3] / "frontend" / "apps" / "dashboard" / "dist"
)


def build_miniapp_app() -> FastAPI:
    miniapp = FastAPI(title="JobMonitor Mini App")
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
    miniapp.include_router(search_profile_router)
    return miniapp


app = build_miniapp_app()
