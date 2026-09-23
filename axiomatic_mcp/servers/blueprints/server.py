"""AxBlueprints MCP server — Axiomatic's catalog of component blueprints and their contracts."""

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.blueprint_service import BlueprintService

mcp = FastMCP(
    name="AxBlueprints Server",
    instructions="""This server exposes Axiomatic's blueprints: versioned contracts for device
    components (an MMI, a Y-junction, a travelling-wave electrode...), each identified by an id of
    the form "<domain>/<name>", e.g. "photonics/mmi".

    Start with list_blueprints for the catalog — one line per blueprint with its lifecycle status,
    component type, port counts and the sections it has. Then call get_blueprint with the id to read
    its contract. By default that returns the structured manifest (ports, modes, parameters,
    budgets, dependencies) and the STATE section; the other sections (readme, validity, source,
    decisions, eval, verification) are opt-in through `sections`, because a full contract runs to
    tens of kilobytes. Ask only for what the task needs.

    Always read a blueprint's status before relying on it. Only "verified", "canonical" and
    "published" mean the blueprint has been validated; every other status, and in particular
    "scaffolded", means it has NOT. At the moment every blueprint in the catalog is "scaffolded", so
    none of them is verified: never cite a blueprint as validated or its numbers as checked results,
    and say so when a plan depends on one.

    A blueprint's contract is what these tools return, nothing more. Do not look for blueprints on
    disk, and do not guess ids — an unknown id comes back as an error listing the ids that exist.
    """
    + get_feedback_prompt(["list_blueprints", "get_blueprint"]),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

blueprint_service = BlueprintService()

BlueprintSection = Literal["manifest", "readme", "state", "validity", "source", "decisions", "eval", "verification"]

_VALIDATED_STATUSES = frozenset({"verified", "canonical", "published"})


def _status_label(status: str | None) -> str:
    if status in _VALIDATED_STATUSES:
        return str(status)
    return f"{status or 'unknown'} (NOT verified)"


def _format_catalog(response: dict[str, Any]) -> str:
    items = response.get("items") or []
    if not items:
        return "No blueprints match these filters."

    width = max(len(str(item.get("id", ""))) for item in items)
    lines = [f"{response.get('total', len(items))} blueprint(s):"]
    for item in items:
        lines.append(
            f"  {str(item.get('id', '')).ljust(width)}  [{_status_label(item.get('status'))}, v{item.get('version', '?')}]  "
            f"{item.get('component_type', '')}, {item.get('n_optical', 0)} optical / {item.get('n_electrical', 0)} electrical port(s); "
            f"sections: {', '.join(item.get('available_sections') or [])}"
        )
    unverified = sum(1 for item in items if item.get("status") not in _VALIDATED_STATUSES)
    if unverified:
        lines.append(f"\n{unverified} of {len(items)} are not verified — do not present them as validated.")
    lines.append("Read one with get_blueprint(blueprint_id=...).")
    return "\n".join(lines)


def _format_manifest_summary(manifest: dict[str, Any]) -> str:
    port_map = manifest.get("port_map") or {}
    ports = manifest.get("ports") or []
    lines = [f"Ports ({manifest.get('n_optical', 0)} optical, {manifest.get('n_electrical', 0)} electrical):"]
    for port in ports:
        name = port.get("name", "")
        description = f": {port_map[name]}" if name in port_map else ""
        lines.append(f"  - {name} ({port.get('direction', '?')}, {port.get('domain', 'optical')}){description}")

    modes = manifest.get("modes") or []
    if modes:
        lines.append(f"Modes: {', '.join(str(mode.get('name', '')) for mode in modes)}")

    parameters = manifest.get("parameters") or []
    lines.append(f"Parameters ({len(parameters)}):")
    for parameter in parameters:
        lines.append(f"  - {parameter.get('name', '')} [{parameter.get('units', '')}]: {parameter.get('description', '')}")

    flags = ("reflective", "passive", "reciprocal", "requires_profile")
    lines.append("Properties: " + ", ".join(f"{flag}={'yes' if manifest.get(flag) else 'no'}" for flag in flags))
    depends_on = manifest.get("depends_on") or []
    lines.append(f"Depends on: {', '.join(depends_on) if depends_on else 'nothing'}")
    lines.append(f"Verified at: {manifest.get('verified_at') or 'never'}")
    lines.append("The full manifest (budgets, conventions, notes) is in the structured result.")
    return "\n".join(lines)


def _format_blueprint(response: dict[str, Any]) -> str:
    status = response.get("status")
    lines = [
        f"{response.get('id', '')} — {response.get('component_type', '')}, version {response.get('version', '?')}",
        f"Status: {_status_label(status)}",
    ]
    if status not in _VALIDATED_STATUSES:
        lines.append("This blueprint has not been validated: do not present it, or any number derived from it, as a checked result.")

    manifest = response.get("manifest")
    sections = response.get("sections") or {}
    fetched = set(sections) | ({"manifest"} if manifest is not None else set())
    not_fetched = [s for s in response.get("available_sections") or [] if s not in fetched]
    if not_fetched:
        lines.append(f"Not fetched: {', '.join(not_fetched)} — pass them in `sections` to read them.")

    if manifest is not None:
        lines.append("\n## Manifest summary\n")
        lines.append(_format_manifest_summary(manifest))
    for section, markdown in sections.items():
        lines.append(f"\n## Section: {section}\n")
        lines.append(markdown)
    return "\n".join(lines)


def _split_blueprint_id(blueprint_id: str) -> tuple[str, str]:
    domain, _, name = blueprint_id.strip().strip("/").partition("/")
    if not domain or not name or "/" in name:
        raise ToolError(
            f"Invalid blueprint id {blueprint_id!r}: expected '<domain>/<name>', e.g. 'photonics/mmi'. "
            "Call list_blueprints for the ids that exist."
        )
    return domain, name


@mcp.tool(
    name="list_blueprints",
    description=(
        "List Axiomatic's component blueprints: one entry per blueprint with its id "
        "('<domain>/<name>', e.g. 'photonics/mmi'), lifecycle status, version, component type, "
        "optical/electrical port counts and the sections available to get_blueprint. Optionally "
        "filter by domain and/or status. Check the status before relying on a blueprint: "
        "'scaffolded' means it has not been validated."
    ),
    tags=["blueprints", "catalog"],
)
async def list_blueprints(
    domain: Annotated[str | None, "Only blueprints of this domain, e.g. 'photonics'"] = None,
    status: Annotated[str | None, "Only blueprints with this lifecycle status, e.g. 'verified' or 'scaffolded'"] = None,
) -> ToolResult:
    """List the blueprint catalog."""
    try:
        response = blueprint_service.list_blueprints(domain, status)
    except Exception as e:
        raise ToolError(f"Failed to list blueprints: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_catalog(response))],
        structured_content=response,
    )


@mcp.tool(
    name="get_blueprint",
    description=(
        "Read one blueprint's contract by id ('<domain>/<name>', as returned by list_blueprints). "
        "With no `sections` it returns the manifest (summarized in the text, complete in the "
        "structured result) and the STATE section. Other sections — readme, validity, source, "
        "decisions, eval, verification — are opt-in: request only the ones the task needs, since "
        "all of them together can reach ~50 KB. Asking for a section the blueprint does not have "
        "fails with the list of sections it does have; an unknown id fails with the ids that exist."
    ),
    tags=["blueprints", "contract"],
)
async def get_blueprint(
    blueprint_id: Annotated[str, "Blueprint id '<domain>/<name>', e.g. 'photonics/mmi'"],
    sections: Annotated[
        list[BlueprintSection] | None,
        "Sections to return. Omit for manifest + state.",
    ] = None,
) -> ToolResult:
    """Read one blueprint's contract."""
    domain, name = _split_blueprint_id(blueprint_id)
    try:
        response = blueprint_service.get_blueprint(domain, name, sections)
    except Exception as e:
        raise ToolError(f"Failed to get blueprint {blueprint_id!r}: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_blueprint(response))],
        structured_content=response,
    )
