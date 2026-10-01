"""Маршруты сайта и мини-аппа, по файлу на раздел."""

from fastapi import APIRouter

from app.telegram.miniapp.routes.export import router as export_router
from app.telegram.miniapp.routes.profile import router as profile_router
from app.telegram.miniapp.routes.public import router as public_router
from app.telegram.miniapp.routes.stats import router as stats_router

router = APIRouter()
router.include_router(public_router)
router.include_router(profile_router)
router.include_router(stats_router)
router.include_router(export_router)
