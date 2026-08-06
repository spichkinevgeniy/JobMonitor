"""Защита от PDF-бомб: маленький файл не должен разворачиваться в гигабайты."""

import asyncio
import io
import time
from types import SimpleNamespace

import fitz  # type: ignore[import-untyped]
import pytest

from app.infrastructure.parsers.exceptions import ParserError, TooManyPagesError
from app.infrastructure.parsers.pdf_parser import (
    MAX_PAGE_PIXELS,
    MAX_RESUME_PAGES,
    PDFParser,
)

A4_INCHES = (8.27, 11.7)


def _make_pdf(pages: int, width_inches: float, height_inches: float) -> bytes:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=width_inches * 72, height=height_inches * 72)
    data: bytes = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def parser() -> PDFParser:
    return PDFParser()


class TestPageCountLimit:
    def test_rejects_document_over_page_limit(self, parser: PDFParser) -> None:
        data = _make_pdf(MAX_RESUME_PAGES + 1, *A4_INCHES)

        with pytest.raises(TooManyPagesError):
            parser._pdf_to_images_and_text(data)

    def test_rejects_before_rendering_anything(
        self, parser: PDFParser, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rendered = []
        monkeypatch.setattr(
            PDFParser, "_render_page", lambda self, page, dpi: rendered.append(page.number)
        )

        with pytest.raises(TooManyPagesError):
            parser._pdf_to_images_and_text(_make_pdf(500, *A4_INCHES))

        assert rendered == []

    def test_accepts_document_at_page_limit(self, parser: PDFParser) -> None:
        images, _ = parser._pdf_to_images_and_text(_make_pdf(MAX_RESUME_PAGES, *A4_INCHES))

        assert len(images) == MAX_RESUME_PAGES


class TestPagePixelBudget:
    def test_normal_page_keeps_requested_dpi(self, parser: PDFParser) -> None:
        with fitz.open(stream=_make_pdf(1, *A4_INCHES), filetype="pdf") as doc:
            assert parser._fit_dpi_to_budget(doc[0], 150) == 150

    def test_oversized_page_is_downscaled(self, parser: PDFParser) -> None:
        with fitz.open(stream=_make_pdf(1, 40, 40), filetype="pdf") as doc:
            fitted = parser._fit_dpi_to_budget(doc[0], 150)

        assert fitted is not None
        assert fitted < 150
        assert 40 * fitted * 40 * fitted <= MAX_PAGE_PIXELS

    def test_absurd_page_is_skipped(self, parser: PDFParser) -> None:
        with fitz.open(stream=_make_pdf(1, 200, 200), filetype="pdf") as doc:
            assert parser._fit_dpi_to_budget(doc[0], 150) is None

    def test_degenerate_page_is_skipped(self, parser: PDFParser) -> None:
        """fitz правит нулевой MediaBox на Letter, поэтому подаём страницу напрямую."""
        page = SimpleNamespace(rect=SimpleNamespace(width=0.0, height=0.0))

        assert parser._fit_dpi_to_budget(page, 150) is None

    def test_bomb_stays_within_memory_budget(self, parser: PDFParser) -> None:
        data = _make_pdf(MAX_RESUME_PAGES, 40, 40)
        assert len(data) < 100 * 1024

        started = time.monotonic()
        images, _ = parser._pdf_to_images_and_text(data)
        elapsed = time.monotonic() - started

        total_pixels = sum(img.width * img.height for img in images)
        for img in images:
            img.close()

        assert total_pixels <= MAX_RESUME_PAGES * MAX_PAGE_PIXELS
        assert elapsed < 30


class TestSignatureCheck:
    async def test_rejects_non_pdf_content(self, parser: PDFParser) -> None:
        with pytest.raises(ParserError):
            await parser.extract_text(io.BytesIO(b"PK\x03\x04 not a pdf at all"))

    async def test_rejects_empty_file(self, parser: PDFParser) -> None:
        with pytest.raises(ParserError):
            await parser.extract_text(io.BytesIO(b""))

    def test_accepts_leading_junk_before_signature(self, parser: PDFParser) -> None:
        parser._ensure_pdf_signature(b"\n\n" + _make_pdf(1, *A4_INCHES))


class TestRenderRunsOffLoop:
    async def test_render_is_dispatched_to_thread(
        self, parser: PDFParser, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def slow_render(data: bytes, dpi: int = 150) -> tuple[list, str]:
            time.sleep(0.5)
            return [], ""

        monkeypatch.setattr(parser, "_pdf_to_images_and_text", slow_render)

        ticks = 0

        async def ticker() -> None:
            nonlocal ticks
            while True:
                await asyncio.sleep(0.01)
                ticks += 1

        task = asyncio.create_task(ticker())
        try:
            with pytest.raises(ParserError):
                await parser.extract_text(io.BytesIO(_make_pdf(1, *A4_INCHES)))
        finally:
            task.cancel()

        assert ticks > 5
