import io
from datetime import datetime

import fitz
from PIL import Image
from pydantic_ai import BinaryContent

from app.application.dto import OutResumeParse, OutResumeSalaryParse
from app.core.logger import get_app_logger
from app.domain.shared.value_objects import Salary
from app.infrastructure.llm import get_resume_parse_agent, get_resume_salary_agent
from app.infrastructure.parsers.base import BaseResumeParser, ParserInput
from app.infrastructure.parsers.exceptions import NotAResumeError, ParserError, TooManyPagesError

logger = get_app_logger(__name__)


class PDFParser(BaseResumeParser):
    def __init__(self) -> None:
        self._resume_agent = get_resume_parse_agent()
        self._salary_agent = get_resume_salary_agent()

    async def extract_text(self, source: ParserInput) -> OutResumeParse:
        if not isinstance(source, io.BytesIO):
            raise ParserError(f"PDFParser expects BytesIO, got {type(source)}")

        logger.info("Resume parsing started")
        images, pdf_text = self._pdf_to_images_and_text(source)

        if not images:
            raise ParserError("Unable to render images from PDF")
        if len(images) > 10:
            logger.warning("Resume rejected: too many pages (%d)", len(images))
            raise TooManyPagesError("Resume is too long (more than 10 pages)")

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

    def _pdf_to_images_and_text(
        self, source: io.BytesIO, dpi: int = 150
    ) -> tuple[list[Image.Image], str]:
        source.seek(0)
        images: list[Image.Image] = []
        text_parts: list[str] = []

        try:
            with fitz.open(stream=source.read(), filetype="pdf") as doc:
                for page in doc:
                    img = self._render_page(page, dpi)
                    if img:
                        images.append(img)
                    text_parts.append(page.get_text("text"))
        except (fitz.FileDataError, fitz.EmptyFileError) as exc:
            logger.error("Invalid PDF file: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error during PDF rendering: %s", exc)

        return images, "\n".join(part for part in text_parts if part)

    def _render_page(self, page: fitz.Page, dpi: int) -> Image.Image | None:
        try:
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            img.load()
            return img
        except Exception as exc:
            logger.error("Error rendering page %d: %s", page.number, exc)
            return None

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

        result = await self._resume_agent.run(
            user_prompt=prompt_parts,
            metadata={"pipeline": "resume_parse"},
        )
        parsed_data = result.output

        salary_source = "resume_pass" if parsed_data.salary is not None else "none"
        salary_evidence: str | None = None
        if parsed_data.salary is None and pdf_text.strip():
            salary_source, salary_evidence = await self._try_fill_salary(parsed_data, pdf_text)

        amount = parsed_data.salary.amount if parsed_data.salary else None
        currency = (
            parsed_data.salary.currency.value
            if parsed_data.salary and parsed_data.salary.currency
            else None
        )
        logger.info(
            "Resume salary parsed: source=%s, amount=%s, currency=%s, evidence=%s",
            salary_source,
            amount,
            currency,
            self._truncate_text(salary_evidence),
        )

        return parsed_data

    async def _run_salary_agent(self, pdf_text: str) -> OutResumeSalaryParse:
        result = await self._salary_agent.run(
            user_prompt=f"Текст резюме:\n{pdf_text}",
            metadata={"pipeline": "resume_salary_pass"},
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

        currency = salary_result.currency.value if salary_result.currency else None
        parsed_data.salary = Salary.create(amount=salary_result.amount, currency=currency)
        return "salary_pass", salary_result.evidence

    @staticmethod
    def _truncate_text(value: str | None, max_len: int = 140) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        if len(cleaned) <= max_len:
            return cleaned
        return f"{cleaned[:max_len]}..."
