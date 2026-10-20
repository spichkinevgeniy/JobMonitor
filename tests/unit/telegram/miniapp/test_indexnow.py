"""Ключ IndexNow: по нему Яндекс и Bing принимают уведомления о страницах."""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.telegram.miniapp.app import build_miniapp_app
from app.telegram.miniapp.routes.public import INDEXNOW_KEY

WORKFLOW = Path(__file__).resolve().parents[4] / ".github/workflows/deploy-prod.yml"


def test_key_served_as_plain_text() -> None:
    """Поисковик сверяет содержимое файла с ключом из уведомления — один в один."""
    response = TestClient(build_miniapp_app()).get("/indexnow.txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == INDEXNOW_KEY


def test_key_format_matches_protocol() -> None:
    """Протокол принимает 8–128 символов: латиница, цифры и дефис."""
    assert re.fullmatch(r"[a-zA-Z0-9-]{8,128}", INDEXNOW_KEY)


def test_deploy_notifies_with_served_key() -> None:
    """Выкладка берёт ключ с того же адреса, по которому его отдаёт сайт."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "$SITE/indexnow.txt" in workflow
    assert "keyLocation" in workflow
