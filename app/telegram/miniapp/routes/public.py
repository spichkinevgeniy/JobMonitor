"""Публичный сайт: рынок, политика и служебные файлы, без Telegram и авторизации."""

from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from app.application.ports.observability_port import Feature
from app.application.services.market_stats_service import MarketSnapshot
from app.core.config import config
from app.infrastructure.observability import observe_feature
from app.telegram.bot.views import BOT_HANDLE, SUPPORT_BOT_HANDLE
from app.telegram.miniapp.deps import get_market_snapshot
from app.telegram.miniapp.market_facts import build_findings, build_json_ld, build_llms_txt
from app.telegram.miniapp.market_page import build_market_context
from app.telegram.miniapp.ui import templates

PRIVACY_UPDATED_AT = "4 октября 2026"

router = APIRouter()


@router.get("/privacy", response_class=HTMLResponse, name="privacy")
async def privacy_page(request: Request) -> HTMLResponse:
    """Публичная страница: открывается и вне Telegram, авторизации не требует."""
    return templates.TemplateResponse(
        request,
        "pages/privacy.html",
        {
            "updated_at": PRIVACY_UPDATED_AT,
            "operator_name": config.PRIVACY_OPERATOR_NAME,
            "support_handle": SUPPORT_BOT_HANDLE,
            "contact_email": config.PRIVACY_CONTACT_EMAIL,
        },
    )


@router.get("/", response_class=HTMLResponse, name="market")
async def market_page(
    request: Request,
    snapshot: Annotated[MarketSnapshot, Depends(get_market_snapshot)],
) -> HTMLResponse:
    """Публичная страница: срез рынка по вакансиям из Telegram, без авторизации."""
    observe_feature(Feature.MARKET_VIEW)
    canonical_url = f"{_public_origin(request)}/"
    return templates.TemplateResponse(
        request,
        "pages/market.html",
        {
            **build_market_context(snapshot),
            "findings": build_findings(snapshot),
            "json_ld": build_json_ld(snapshot, canonical_url),
            "canonical_url": canonical_url,
            "bot_url": _telegram_url(BOT_HANDLE),
        },
    )


@router.get("/llms.txt", response_class=PlainTextResponse, include_in_schema=False)
async def llms_txt(
    request: Request,
    snapshot: Annotated[MarketSnapshot, Depends(get_market_snapshot)],
) -> str:
    """Справка о сайте для ИИ-ассистентов: что это и главные цифры."""
    return build_llms_txt(snapshot, _public_origin(request), _telegram_url(BOT_HANDLE))


@router.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
async def robots_txt(request: Request) -> str:
    # Мини-апп без Telegram бесполезен, в поиске ему делать нечего.
    return f"User-agent: *\nDisallow: /miniapp\n\nSitemap: {_public_origin(request)}/sitemap.xml\n"


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml(request: Request) -> Response:
    origin = _public_origin(request)
    urls = "".join(f"<url><loc>{origin}{path}</loc></url>" for path in ("/", "/privacy"))
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    )
    return Response(body, media_type="application/xml")


def _public_origin(request: Request) -> str:
    """Адрес сайта для ссылок наружу.

    За nginx приложение видит себя по http и внутреннему адресу, поэтому
    домен берётся из настроек, а запрос — только запасной вариант.
    """
    parsed = urlsplit(config.MINI_APP_BASE_URL.strip())
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return str(request.base_url).rstrip("/")


def _telegram_url(handle: str) -> str:
    return f"https://t.me/{handle.removeprefix('@')}"
