import os

from app.infrastructure.parsers.base import BaseResumeParser
from app.infrastructure.parsers.pdf_parser import PDFParser


class ParserFactory:
    _extension_map: dict[str, type[BaseResumeParser]] = {".pdf": PDFParser}

    @classmethod
    def get_parser_by_extension(
        cls,
        file_name: str,
    ) -> BaseResumeParser:
        _, ext = os.path.splitext(file_name.lower())

        parser_cls = cls._extension_map.get(ext)
        if parser_cls is None:
            raise ValueError(f"Extension {ext} is not supported")
        return parser_cls()
