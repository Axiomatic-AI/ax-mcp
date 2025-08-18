import asyncio
from pathlib import Path

from pydantic import BaseModel, Field

from ...shared.api_client import AxiomaticAPIClient


class ParseResponse(BaseModel):
    markdown: str = Field(description="The extracted Markdown text, equations as latex, and images as base64 encoded strings.")
    images: dict[str, str] = Field(default_factory=dict, description="Images as base64 encoded strings")
    interline_equations: list[str] = Field(default_factory=list, description="Interline equations as latex")
    inline_equations: list[str] = Field(
        default_factory=list,
        description="Inline equations as latex",
    )


async def pdf_to_markdown(file_path: Path) -> ParseResponse:
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError("File must be a PDF")

    file_content = await asyncio.to_thread(file_path.read_bytes)
    files = {"file": (file_path.name, file_content, "application/pdf")}
    params = {"method": "mistral", "ocr": False, "layout_model": "doclayout_yolo"}

    response = await asyncio.to_thread(
        AxiomaticAPIClient().post,
        "/document/parse",
        files=files,
        params=params,
    )

    return ParseResponse(**response)
