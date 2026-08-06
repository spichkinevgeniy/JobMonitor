import asyncio
import io
import math
from datetime import datetime

import fitz  # type: ignore[import-untyped]
from PIL import Image
from pydantic_ai import BinaryContent

from app.application.dto import OutResumeParse, OutResumeSalaryParse
from app.core.logger import get_app_logger
from app.domain.shared.value_objects import Salary
from app.infrastructure.llm import get_resume_parse_agent, get_resume_salary_agent
from app.infrastructure.llm_runtime import run_with_llm_retry
from app.infrastructure.parsers.base import BaseResumeParser, ParserInput
from app.infrastructure.parsers.exceptions import NotAResumeError, ParserError, TooManyPagesError

logger = get_app_logger(__name__)

MAX_RESUME_SKILLS = 6
MAX_RESUME_SPECIALIZATIONS = 3
MIN_EVIDENCE_LENGTH = 3

MAX_RESUME_PAGES = 10
# Бюджет на страницу: A4 при 150 dpi — это 2.2 млн пикселей, так что запас
# есть даже под A3. Страница крупнее рендерится с пониженным dpi.
MAX_PAGE_PIXELS = 4_000_000
MIN_RENDER_DPI = 40
RENDER_TIMEOUT_SECONDS = 60
PDF_SIGNATURE = b"%PDF-"
PDF_SIGNATURE_SEARCH_BYTES = 1024


class PDFParser(BaseResumeParser):
    def __init__(self) -> None:
        self._resume_agent = get_resume_parse_agent()
        self._salary_agent = get_resume_salary_agent()

    async def extract_text(self, source: ParserInput) -> OutResumeParse:
        if not isinstance(source, io.BytesIO):
            raise ParserError(f"PDFParser expects BytesIO, got {type(source)}")

        source.seek(0)
        raw = source.read()
        self._ensure_pdf_signature(raw)

        logger.info("Resume parsing started")
        # Рендер синхронный и тяжёлый, а процесс у нас один на бота, скрапер и
        # рассылку — без отдельного потока тяжёлое резюме подвешивает всех.
        # Таймаут тут страховочный: поток не прервать, но лимиты страниц и
        # пикселей и так держат работу конечной.
        try:
            images, pdf_text = await asyncio.wait_for(
                asyncio.to_thread(self._pdf_to_images_and_text, raw),
                timeout=RENDER_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            logger.warning("Resume rejected: rendering timed out")
            raise ParserError("PDF rendering timed out") from None

        if not images:
            raise ParserError("Unable to render images from PDF")

        try:
            logger.info("Resume images ready: %d pages", len(images))
            parsed_data = await self._run_agent(images, pdf_text)
        finally:
            for img in images:
                img.close()
            images.clear()

        if not parsed_data.is_resume:
            logger.info("Resume parsing completed: not a resume")
            raise NotAResumeError("Document is not recognized as a resume")

        logger.info("Resume parsing completed: success")
        return parsed_data

    def _pdf_to_images_and_text(self, data: bytes, dpi: int = 150) -> tuple[list[Image.Image], str]:
        images: list[Image.Image] = []
        text_parts: list[str] = []

        try:
            with fitz.open(stream=data, filetype="pdf") as doc:
                # Считаем страницы до рендера: 500 пустых страниц весят 80 КБ,
                # но отрисовка каждой стоит памяти и секунд.
                if doc.page_count > MAX_RESUME_PAGES:
                    logger.warning("Resume rejected: too many pages (%d)", doc.page_count)
                    raise TooManyPagesError(
                        f"Resume is too long (more than {MAX_RESUME_PAGES} pages)"
                    )
                for page in doc:
                    img = self._render_page(page, dpi)
                    if img:
                        images.append(img)
                    text_parts.append(page.get_text("text"))
        except TooManyPagesError:
            raise
        except (fitz.FileDataError, fitz.EmptyFileError):
            logger.exception("Invalid PDF file")
        except Exception:
            logger.exception("Unexpected error during PDF rendering")

        return images, "\n".join(part for part in text_parts if part)

    def _render_page(self, page: fitz.Page, dpi: int) -> Image.Image | None:
        render_dpi = self._fit_dpi_to_budget(page, dpi)
        if render_dpi is None:
            logger.warning(
                "Page %d skipped: too large to render (%.0fx%.0f pt)",
                page.number,
                page.rect.width,
                page.rect.height,
            )
            return None

        try:
            pix = page.get_pixmap(dpi=render_dpi)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            img.load()
            return img
        except Exception:
            logger.exception("Error rendering page %d", page.number)
            return None

    @staticmethod
    def _fit_dpi_to_budget(page: fitz.Page, dpi: int) -> int | None:
        """Понижает dpi, чтобы растр страницы влез в бюджет пикселей.

        Размер страницы задаётся в самом PDF, спека допускает до 200x200
        дюймов. На 150 dpi такая страница разворачивается в 2.7 ГБ, хотя
        файл весит меньше килобайта. Возвращает None, если даже на
        минимальном dpi страница не влезает — читать её всё равно нечем.
        """
        width_inches = page.rect.width / 72
        height_inches = page.rect.height / 72
        if width_inches <= 0 or height_inches <= 0:
            return None

        pixels = width_inches * height_inches * dpi * dpi
        if pixels <= MAX_PAGE_PIXELS:
            return dpi

        fitted = int(dpi * math.sqrt(MAX_PAGE_PIXELS / pixels))
        return fitted if fitted >= MIN_RENDER_DPI else None

    @staticmethod
    def _ensure_pdf_signature(data: bytes) -> None:
        """Расширение файла приходит от пользователя, содержимое не проверено.

        Сигнатуру ищем не строго с нулевого байта: ридеры терпят мусор в
        начале файла, и такие резюме реально встречаются.
        """
        if PDF_SIGNATURE not in data[:PDF_SIGNATURE_SEARCH_BYTES]:
            logger.warning("Resume rejected: no PDF signature")
            raise ParserError("File is not a PDF")

    async def _run_agent(self, images: list[Image.Image], pdf_text: str) -> OutResumeParse:
        current_date = datetime.now().strftime("%B %Y")
        prompt_parts: list[str | BinaryContent] = [
            f"Current date for calculations: {current_date}\n"
            "Analyze the resume using both sources below.\n\n"
            "PDF text layer:\n"
            f"{pdf_text}\n\n"
            "Resume page images:",
        ]

        for idx, img in enumerate(images, start=1):
            image_to_use = img
            if img.mode in ("RGBA", "P"):
                image_to_use = img.convert("RGB")

            img_byte_arr = io.BytesIO()
            image_to_use.save(img_byte_arr, format="JPEG", quality=85, optimize=True)
            img_bytes = img_byte_arr.getvalue()
            prompt_parts.append(BinaryContent(data=img_bytes, media_type="image/jpeg"))

            logger.debug(
                "Prepared image %d: size=%.2f KB (JPEG)",
                idx,
                len(img_bytes) / 1024,
            )

            img_byte_arr.close()
            if image_to_use is not img:
                image_to_use.close()

        result = await run_with_llm_retry(
            "resume_parse",
            lambda: self._resume_agent.run(
                user_prompt=prompt_parts,
                metadata={"pipeline": "resume_parse"},
            ),
        )
        parsed_data = result.output
        self._sanitize_extracted_profile(parsed_data)

        salary_source = "resume_pass" if parsed_data.salary_amount is not None else "none"
        salary_evidence: str | None = None
        if parsed_data.salary_amount is None and pdf_text.strip():
            salary_source, salary_evidence = await self._try_fill_salary(parsed_data, pdf_text)

        amount = parsed_data.salary_amount
        currency = parsed_data.salary_currency.value if parsed_data.salary_currency else None
        logger.info(
            "Resume salary parsed: source=%s, amount=%s, currency=%s, evidence=%s",
            salary_source,
            amount,
            currency,
            self._truncate_text(salary_evidence),
        )

        return parsed_data

    async def _run_salary_agent(self, pdf_text: str) -> OutResumeSalaryParse:
        result = await run_with_llm_retry(
            "resume_salary_pass",
            lambda: self._salary_agent.run(
                user_prompt=f"Текст резюме:\n{pdf_text}",
                metadata={"pipeline": "resume_salary_pass"},
            ),
        )
        return result.output

    async def _try_fill_salary(
        self, parsed_data: OutResumeParse, pdf_text: str
    ) -> tuple[str, str | None]:
        try:
            salary_result = await self._run_salary_agent(pdf_text)
        except Exception:
            logger.exception("Salary second pass failed")
            return "none", None

        if salary_result.amount is None:
            return "none", salary_result.evidence

        normalized = Salary.create(
            amount=salary_result.amount,
            currency=salary_result.currency.value if salary_result.currency else None,
        )
        parsed_data.salary_amount = normalized.amount
        parsed_data.salary_currency = normalized.currency
        return "salary_pass", salary_result.evidence

    def _sanitize_extracted_profile(self, parsed_data: OutResumeParse) -> None:
        """Defense-in-depth поверх LLM: не полагаемся только на промпт.

        Отбрасывает specializations/skills без реальной цитаты-обоснования и
        обрезает списки до разумного максимума, если модель всё равно
        вернула слишком много (это признак "выбрала всё подряд", а не
        реального богатого профиля).
        """
        original_specializations = len(parsed_data.specializations)
        original_skills = len(parsed_data.skills)

        parsed_data.specializations = [
            item
            for item in parsed_data.specializations
            if len(item.evidence.strip()) >= MIN_EVIDENCE_LENGTH
        ][:MAX_RESUME_SPECIALIZATIONS]

        parsed_data.skills = [
            item for item in parsed_data.skills if len(item.evidence.strip()) >= MIN_EVIDENCE_LENGTH
        ][:MAX_RESUME_SKILLS]

        if len(parsed_data.specializations) != original_specializations or (
            len(parsed_data.skills) != original_skills
        ):
            logger.warning(
                "Resume profile sanitized: specializations %d->%d, skills %d->%d",
                original_specializations,
                len(parsed_data.specializations),
                original_skills,
                len(parsed_data.skills),
            )

    @staticmethod
    def _truncate_text(value: str | None, max_len: int = 140) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        if len(cleaned) <= max_len:
            return cleaned
        return f"{cleaned[:max_len]}..."
