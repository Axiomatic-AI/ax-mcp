import asyncio
import mimetypes
import textwrap
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated

import filetype
from fastmcp import FastMCP
from fastmcp.exceptions import NotFoundError, ToolError, ValidationError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from pydantic import BaseModel, Field, field_validator

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.api_client import AxiomaticAPIClient
from ...shared.utils.prompt_utils import get_feedback_prompt

mimetypes.add_type("text/markdown", ".md")


class AnnotationType(str, Enum):
    TEXT = "text"
    EQUATION = "equation"
    FIGURE_DESCRIPTION = "figure_description"
    PARAMETER = "parameter"


class Annotation(BaseModel):
    """
    Represents an annotation with citation and contextual description.
    An annotation provides broader context and explanation for a citation.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the annotation",
    )
    annotation_type: AnnotationType = Field(..., description="Type of annotation")
    description: str = Field(..., description="Broader contextual description of the citation")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: datetime = Field(default_factory=datetime.now, description="When annotation was created")
    equation: str | None = Field(
        None,
        description="The equation in LaTeX format that is relevant to the annotation",
    )
    parameter_name: str | None = Field(
        None,
        description="The name of the parameter that is relevant to the annotation",
    )
    parameter_value: float | None = Field(
        None,
        description="The value of the parameter that is relevant to the annotation",
    )
    parameter_unit: str | None = Field(
        None,
        description="The unit of the parameter that is relevant to the annotation",
    )
    reference: str = Field(
        ...,
        description="The reference to the source that is relevant to the annotation. In APA format.",
    )


class PDFAnnotation(Annotation):
    """
    PDF-specific annotation that includes page location.
    """

    page_number: int = Field(..., description="The page number of the source")


class AnnotationsResponse(BaseModel):
    annotations: list[Annotation]

    @field_validator("annotations", mode="before")
    @classmethod
    def validate_annotations(cls, v):
        if not v:
            return v

        # Check format
        first_item = v[0] if v else {}
        has_page_number = "page_number" in first_item

        if has_page_number:
            return [PDFAnnotation.model_validate(item) for item in v]
        else:
            return [Annotation.model_validate(item) for item in v]


mcp = FastMCP(
    name="AxDocumentAnnotator Server",
    instructions="""This server provides tools to annotate pdfs with detailed analysis.
    """
    + get_feedback_prompt("annotate_pdf"),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)


@mcp.tool(
    name="annotate_file",
    description="Annotate a file with detailed analysis. Supports PDF, PNG, JPEG, MD, and TXT files.",
    tags=["file", "annotate", "analyze"],
)
async def annotate_file(
    file_path: Annotated[Path, "The absolute path to the file to annotate"],
    query: Annotated[str, "The specific instructions or query to use for annotating the file"],
) -> ToolResult:
    return await annotate_file_main(file_path, query)


async def annotate_file_main(file_path: Path, query: str) -> ToolResult:
    if not file_path.exists():
        raise NotFoundError(f"File not found: {file_path}")

    allowed = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "text/markdown",
        "text/plain",
    }

    def _guess_mime(path: Path) -> str | None:
        try:
            if kind := filetype.guess(str(path)):
                return kind.mime
        except Exception:
            pass

        guessed, _ = mimetypes.guess_type(path.name)
        return guessed

    file_type = _guess_mime(file_path)

    if file_type not in allowed:
        raise ValidationError(f"Unsupported file type: {file_path.suffix}. Supported types: pdf, png, jpeg, md, txt.")

    try:
        file_content = await asyncio.to_thread(file_path.read_bytes)
        files = {"file": (file_path.name, file_content, file_type)}
        data = {"query": query}

        response = await asyncio.to_thread(
            AxiomaticAPIClient().post,
            "/annotations/",
            files=files,
            data=data,
        )

        annotations_response = AnnotationsResponse.model_validate(response)
        annotations_text = (
            format_annotations(annotations_response.annotations) if annotations_response.annotations else "No annotations found for the given query."
        )

    except Exception as e:
        raise ToolError(f"Failed to annotate file: {e!s}") from e

    try:
        with (file_path.parent / f"{file_path.stem}_annotations.md").open("w", encoding="utf-8") as f:
            f.write(annotations_text)
    except Exception as e:
        return ToolResult(
            content=[
                TextContent(
                    type="text",
                    text=textwrap.dedent(
                        f"""Successfully annotated {file_path.name}\n\n
                    Failed to save markdown file: {e!s}\n\n
                    **Query:** {query}\n\n
                    **Annotations:**\n\n{annotations_text}"""
                    ),
                )
            ]
        )

    # Return the result
    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=textwrap.dedent(
                    f"""Successfully annotated {file_path.name}\n\n
                    Successfully saved markdown file: {file_path.parent / f"{file_path.stem}_annotations.md"}\n\n
                    **Query:** {query}\n\n
                    **Annotations:**\n\n
                    {annotations_text}"""
                ),
            )
        ]
    )


def format_annotations(annotations: list[Annotation]) -> str:
    annotation_lines = []

    for i, annotation in enumerate(annotations, start=1):
        if hasattr(annotation, "page_number"):
            annotation_lines.append(f"**Annotation {i}** (Page {annotation.page_number}):")
        else:
            annotation_lines.append(f"**Annotation {i}**:")
        annotation_lines.append(f"Type: {annotation.annotation_type}")

        annotation_lines.append(f"Description: {annotation.description}")

        if annotation.equation:
            annotation_lines.append(f"Equation: {annotation.equation}")
        if annotation.parameter_name:
            param_info = f"Parameter: {annotation.parameter_name}"
            if annotation.parameter_value is not None:
                param_info += f" = {annotation.parameter_value}"
            if annotation.parameter_unit:
                param_info += f" {annotation.parameter_unit}"

            annotation_lines.append(param_info)
        if annotation.tags:
            annotation_lines.append(f"Tags: {', '.join(annotation.tags)}")

        if hasattr(annotation, "reference") and annotation.reference:
            annotation_lines.append(f"Reference: {annotation.reference}")

        annotation_lines.append("")

    annotations_text = "\n".join(annotation_lines)
    return annotations_text
