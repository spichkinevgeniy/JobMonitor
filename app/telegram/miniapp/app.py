from pathlib import Path

import logfire
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.telegram.miniapp.routes import router
from app.telegram.miniapp.ui import STATIC_DIR

SHELL_DIST_DIR = (
    Path(__file__).resolve().parents[3] / "frontend" / "apps" / "shell" / "dist"
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
    miniapp.include_router(router)
    return miniapp


app = build_miniapp_app()
