import asyncio

from pathlib import Path
from fastmcp import FastMCP
from mcp.types import Annotated, TextContent
from fastmcp.tools.tool import ToolResult, ToolError
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from ...shared.api_client import AxiomaticAPIClient

class AnnotationType(str, Enum):
    TEXT = "text"
    EQUATION = "equation"
    FIGURE_DESCRIPTION = "figure_description"
    
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
    created_at: datetime = Field(
        default_factory=datetime.now, description="When annotation was created"
    )


class PDFAnnotation(Annotation):
    """
    Represents an annotation with citation and contextual description.
    An annotation provides broader context and explanation for a citation.
    """

    page_number: int = Field(..., description="The page number of the source")
    equation: Optional[str] = Field(
        None,
        description="The equation in LaTeX format that is relevant to the annotation",
    )
    parameter_value: Optional[float] = Field(
        None,
        description="The value of the parameter that is relevant to the annotation",
    )
    parameter_name: Optional[str] = Field(
        None, description="The name of the parameter that is relevant to the annotation"
    )
    parameter_unit: Optional[str] = Field(
        None, description="The unit of the parameter that is relevant to the annotation"
    )

class AnnotationsResponse(BaseModel):
    annotations: list[PDFAnnotation]


mcp = FastMCP(
    name="Axiomatic Annotations",
    instructions="""This server provides tools to annotate pdfs with detailed analysis.""",
    version="0.0.1",
)

@mcp.tool(
    name="annotate_pdf",
    description="Annotate a pdf with detailed analysis.",
    tags=["pdf", "annotate", "analyze"],
)
async def annotate_file(
    file_path: Annotated[Path, "The absolute path to the pdf file to annotate"],
    query: Annotated[str, "The specific instructions or query to use for annotating the file"],
) -> ToolResult:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")    
    if file_path.suffix.lower() != ".pdf":
        raise ValueError("File must be a PDF")

    try: 
        file_content = await asyncio.to_thread(file_path.read_bytes)
        files = {"file": (file_path.name, file_content, "application/pdf")}
        data = {"query": query}

        response = await asyncio.to_thread(
                AxiomaticAPIClient().post,
                "/annotations/",
                files=files,
                data=data,
        )

        if not response.annotations:
            annotations_text = "No annotations found for the given query."
        else:
            annotations_text = format_annotations(response.annotations)

        return ToolResult(
            content=[
                TextContent(
                    type="text", 
                    text=f"Successfully annotated {file_path.name}\n\n**Query:** {query}\n\n**Annotations:**\n\n{annotations_text}"
                )
            ]
        )
    except Exception as e:
        raise ToolError(f"Failed to annotate file: {e!s}") from e

def format_annotations(annotation_lines: list[str], annotations: list[PDFAnnotation]) -> str:
    annotation_lines = []

    for i, annotation in enumerate(annotations):
        annotation_lines.append(f"**Annotation {i}** (Page {annotation.page_number}):")
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
        
        annotation_lines.append("")
    
    annotations_text = "\n".join(annotation_lines)
    return annotations_text