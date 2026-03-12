import logfire
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.telegram.miniapp.routes import router
from app.telegram.miniapp.ui import STATIC_DIR


def build_miniapp_app() -> FastAPI:
    miniapp = FastAPI(title="JobMonitor Mini App")
    logfire.instrument_fastapi(miniapp)
    miniapp.mount("/miniapp/static", StaticFiles(directory=str(STATIC_DIR)), name="miniapp-static")
    miniapp.include_router(router)
    return miniapp


app = build_miniapp_app()
