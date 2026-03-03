from abc import ABC, abstractmethod
from io import BytesIO
from typing import Union

from app.application.dto import OutResumeParse

ParserInput = Union[BytesIO, str]


class BaseResumeParser(ABC):
    @abstractmethod
    async def extract_text(self, source: ParserInput) -> OutResumeParse: ...
