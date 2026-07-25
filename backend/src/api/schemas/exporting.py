from enum import Enum

from pydantic import BaseModel


class ExportFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"


class ExportRequest(BaseModel):
    format: ExportFormat
    include_citations: bool = True
