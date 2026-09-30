"""Выгрузка вакансий файлом в чат с ботом."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.application.dto.miniapp import ExportRequest, SaveResponse
from app.application.ports.observability_port import Feature
from app.application.services.export_service import ExportFormat, ExportService
from app.infrastructure.notifications import TelegramDocumentSender
from app.infrastructure.observability import observe_feature
from app.telegram.miniapp.deps import get_document_sender, get_export_service, parse_user_context
from app.telegram.miniapp.throttle import (
    cancel_export,
    register_export,
    seconds_until_export_allowed,
)

_EXPORT_FEATURES = {
    ExportFormat.JSON: Feature.EXPORT_JSON,
    ExportFormat.MARKDOWN: Feature.EXPORT_MARKDOWN,
    ExportFormat.TXT: Feature.EXPORT_TXT,
}

router = APIRouter()


@router.post(
    "/miniapp/api/export",
    name="miniapp-export",
    response_model=SaveResponse,
)
async def export_vacancies(
    payload: ExportRequest,
    service: Annotated[ExportService, Depends(get_export_service)],
    sender: Annotated[TelegramDocumentSender, Depends(get_document_sender)],
) -> SaveResponse:
    user_context = parse_user_context(payload.init_data)

    try:
        export_format = ExportFormat(payload.export_format)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неизвестный формат выгрузки.") from None

    # Проверка и отметка без await между ними, иначе пачка запросов пройдёт целиком.
    retry_after = seconds_until_export_allowed(user_context.tg_id)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail=f"Слишком часто. Повторите через {retry_after} с.",
        )
    register_export(user_context.tg_id)
    observe_feature(_EXPORT_FEATURES[export_format])

    export_file = await service.build(user_context.tg_id, export_format)
    if export_file is None:
        cancel_export(user_context.tg_id)
        raise HTTPException(
            status_code=404,
            detail="Пока нечего выгружать: бот ещё не присылал вам вакансии.",
        )

    await sender.send_document(
        user_tg_id=user_context.tg_id,
        filename=export_file.filename,
        content=export_file.content,
        caption=f"Выгрузка вакансий: {export_file.count} шт.",
    )
    return SaveResponse(message="Файл отправлен в чат с ботом.")
