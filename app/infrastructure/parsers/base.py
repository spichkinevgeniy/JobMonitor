from abc import ABC, abstractmethod
from io import BytesIO

from app.application.dto import OutResumeParse

ParserInput = BytesIO | str


class BaseResumeParser(ABC):
    @abstractmethod
    async def extract_text(self, source: ParserInput) -> OutResumeParse: ...
