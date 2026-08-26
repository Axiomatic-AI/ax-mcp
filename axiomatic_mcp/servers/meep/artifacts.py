"""Decode, summarize and save the artifacts a meep job exports.

``GET /numerics/meep/execute/results/{task_id}`` returns every ``export()`` value
base64-encoded (PNG, ``.npy``, ``.npz``, dill pickle) or as raw text, and never
deserializes server-side. This module does the client-side half: it writes each artifact to
a local file, builds a short human-readable summary instead of echoing the payload (one
field array is hundreds of kilobytes of base64, which would flood the caller's context),
and renders PNG figures as inline images so a model can actually see them.

Pickles are written but never loaded. ``dill`` is deliberately not a dependency of this
package, and a hostile ``__reduce__`` is exactly what we refuse to run.
"""

import base64
import binascii
import io
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from fastmcp.utilities.types import Image
from mcp.types import ImageContent

from ...shared.utils.get_unique_filename import get_unique_filename

OUTPUT_DIR_ENV_VAR = "AXIOMATIC_MEEP_OUTPUT_DIR"

_SUFFIXES = {"png": ".png", "npy": ".npy", "npz": ".npz", "pickle": ".pkl"}
_MAGIC = {"png": b"\x89PNG\r\n\x1a\n", "npy": b"\x93NUMPY", "npz": b"PK\x03\x04"}

_MAX_INLINE_TEXT_CHARS = 2000
_MAX_INLINE_CONSOLE_CHARS = 4000
_CONSOLE_EXCERPT_SIDE_CHARS = 2000
# A single artifact may be up to 50 MB; inlining that as base64 would blow the caller's
# context, so oversized figures are reported by path only.
_MAX_INLINE_IMAGE_BYTES = 3_000_000
_MAX_NPZ_MEMBERS = 20
_MAX_NAME_CHARS = 100
_UNSAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

_PICKLE_NOTE = (
    "NOT decoded here. To read it locally: `import dill; obj = dill.loads(Path(path).read_bytes())` "
    "in an environment holding the job image's libraries — a meep pickle references the meep module "
    "and will not load without pymeep. Prefer re-exporting numbers as arrays or a figure, or printing "
    "them in the script so they land in console_output."
)


@dataclass
class ExportSummary:
    """One export, decoded and described but never deserialized."""

    name: str
    kind: str
    size_bytes: int
    summary: str
    path: Path | None = None
    image: ImageContent | None = None
    failure: str | None = None


def safe_name(name: str) -> str:
    """Reduce an untrusted name to a single safe path segment.

    Export names come straight from user code (``export("...", obj)``) and the task id is a
    raw tool argument, so either can carry path separators or ``..``.
    """
    cleaned = _UNSAFE_NAME_RE.sub("_", name).strip("._-")[:_MAX_NAME_CHARS]
    return cleaned or "export"


def default_output_base() -> Path:
    """Base directory for artifacts: the env var if set, else the process working directory."""
    configured = os.getenv(OUTPUT_DIR_ENV_VAR)
    return Path(configured).expanduser() if configured else Path.cwd()


def resolve_output_dir(task_id: str, override: str | Path | None = None) -> Path:
    """Create and return the per-task artifact directory.

    Each job gets its own ``meep_<task_id>/`` subdirectory, so a geometry preview and a full
    solve that export the same names cannot collide, and two jobs never overwrite each other.
    """
    base = Path(override).expanduser() if override else default_output_base()
    directory = (base / f"meep_{safe_name(task_id)}").resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _artifact_path(directory: Path, name: str, suffix: str) -> Path:
    """Pick a collision-free path for an export, refusing anything outside ``directory``."""
    path = get_unique_filename(directory, f"{safe_name(name)}{suffix}").resolve()
    if not path.is_relative_to(directory):
        raise ValueError(f"refusing to write export {name!r} outside {directory}")
    return path


def _reject_constant(value: str) -> None:
    """Make ``json.loads`` reject NaN/Infinity, which are not valid JSON."""
    raise ValueError(f"not valid JSON: {value}")


def _is_json_text(text: str) -> bool:
    if text.lstrip()[:1] not in ("{", "["):
        return False
    try:
        json.loads(text, parse_constant=_reject_constant)
    except ValueError:
        return False
    return True


def _human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} kB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def describe_array(label: str, arr: np.ndarray) -> str:
    """Summarize an array without printing it.

    Every numeric format sits inside the ``try`` that produces the clean fallback, and each
    ``except`` reports why stats are missing rather than swallowing the error.
    """
    parts = [f"{label}: shape={tuple(arr.shape)}, dtype={arr.dtype}"]
    if arr.size == 0:
        parts.append("(empty)")
    elif arr.size == 1:
        # Exact, never formatted: a 0-d export is usually the scalar the caller cares about.
        parts.append(f"value={arr.reshape(-1)[0].item()!r}")
    elif np.issubdtype(arr.dtype, np.complexfloating):
        try:
            magnitude = np.abs(arr)
            parts.append(f"|z|: min={float(magnitude.min()):.6g}, max={float(magnitude.max()):.6g}, mean={float(magnitude.mean()):.6g}")
        except (ValueError, TypeError) as e:
            parts.append(f"(magnitude stats unavailable: {type(e).__name__})")
    elif np.issubdtype(arr.dtype, np.bool_):
        parts.append(f"true={int(arr.sum())} of {arr.size}")
    elif np.issubdtype(arr.dtype, np.number):
        try:
            finite = arr[np.isfinite(arr)]
            if finite.size == 0:
                parts.append("all values non-finite (nan/inf)")
            else:
                parts.append(f"min={float(finite.min()):.6g}, max={float(finite.max()):.6g}, mean={float(finite.mean()):.6g}")
                if finite.size != arr.size:
                    parts.append(f"non-finite={arr.size - finite.size}")
        except (ValueError, TypeError) as e:
            parts.append(f"(stats unavailable: {type(e).__name__})")
    return ", ".join(parts)


def _excerpt(text: str, limit: int, side: int, note: str) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:side]}\n\n[...{note}...]\n\n{text[-side:]}"


def _summarize_text_export(name: str, payload: str, size: int, directory: Path) -> ExportSummary:
    suffix = ".json" if _is_json_text(payload) else ".txt"
    path = _artifact_path(directory, name, suffix)
    path.write_text(payload, encoding="utf-8")
    if not payload:
        body = "(empty text export)"
    else:
        body = _excerpt(payload, _MAX_INLINE_TEXT_CHARS, _MAX_INLINE_TEXT_CHARS // 2, f"truncated; full text at {path}")
    return ExportSummary(
        name=name,
        kind="text",
        size_bytes=size,
        summary=f"{name} (text, {_human_size(size)}) -> {path}\n{body}",
        path=path,
    )


def _summarize_npy(name: str, data: bytes, size: int, path: Path) -> str:
    try:
        arr = np.load(io.BytesIO(data), allow_pickle=False)
    except (ValueError, OSError, EOFError) as e:
        return f"{name} (npy, {_human_size(size)}) -> {path}\n  could not be read as a numpy array ({type(e).__name__}: {e})"
    return f"{name} (npy, {_human_size(size)}) -> {path}\n  {describe_array('array', arr)}"


def _summarize_npz(name: str, data: bytes, size: int, path: Path) -> str:
    header = f"{name} (npz bundle, {_human_size(size)}) -> {path}"
    try:
        with np.load(io.BytesIO(data), allow_pickle=False) as bundle:
            members = list(bundle.files)
            lines = []
            for member in members[:_MAX_NPZ_MEMBERS]:
                try:
                    lines.append(f"  {describe_array(member, bundle[member])}")
                except (ValueError, OSError, EOFError) as e:
                    lines.append(f"  {member}: unreadable ({type(e).__name__})")
            if len(members) > _MAX_NPZ_MEMBERS:
                lines.append(f"  ... +{len(members) - _MAX_NPZ_MEMBERS} more members")
    except (ValueError, OSError, EOFError) as e:
        return f"{header}\n  could not be read as an npz bundle ({type(e).__name__}: {e})"
    return "\n".join([header, *lines])


def summarize_export(name: str, artifact: dict[str, Any], directory: Path, allow_image: bool) -> ExportSummary:
    """Write one export to ``directory`` and describe it."""
    kind = artifact.get("kind") or "unknown"
    payload = artifact.get("payload") or ""
    declared_size = artifact.get("size_bytes")

    if kind == "text":
        # size_bytes is legitimately 0 for an empty export, so never truthiness-check it.
        size = declared_size if declared_size is not None else len(payload.encode("utf-8"))
        return _summarize_text_export(name, payload, size, directory)

    try:
        data = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as e:
        return ExportSummary(
            name=name,
            kind=kind,
            size_bytes=declared_size or 0,
            summary=f"{name} ({kind}): payload is not valid base64 and was skipped",
            failure=f"decode_error: {type(e).__name__}: {e}",
        )

    size = declared_size if declared_size is not None else len(data)

    # Cross-check the declared kind against the magic bytes: a mislabelled artifact must
    # never reach np.load or be presented as a renderable image.
    expected_magic = _MAGIC.get(kind)
    mislabelled = expected_magic is not None and not data.startswith(expected_magic)
    effective_kind = "pickle" if mislabelled else kind

    suffix = _SUFFIXES.get(effective_kind, ".bin")
    path = _artifact_path(directory, name, suffix)
    path.write_bytes(data)

    if mislabelled:
        summary = (
            f"{name} (declared {kind} but the magic bytes do not match, {_human_size(size)}) -> {path}\n  treated as opaque bytes; {_PICKLE_NOTE}"
        )
        return ExportSummary(name=name, kind=kind, size_bytes=size, summary=summary, path=path)

    if effective_kind == "png":
        summary = f"{name} (png figure, {_human_size(size)}) -> {path}"
        image = None
        if allow_image and len(data) <= _MAX_INLINE_IMAGE_BYTES:
            image = Image(data=data, format="png").to_image_content()
        else:
            summary += "\n  not shown inline (too large or inline image budget spent) — open the file to view it"
        return ExportSummary(name=name, kind=kind, size_bytes=size, summary=summary, path=path, image=image)

    if effective_kind == "npy":
        return ExportSummary(name=name, kind=kind, size_bytes=size, summary=_summarize_npy(name, data, size, path), path=path)

    if effective_kind == "npz":
        return ExportSummary(name=name, kind=kind, size_bytes=size, summary=_summarize_npz(name, data, size, path), path=path)

    if effective_kind == "pickle":
        return ExportSummary(
            name=name,
            kind=kind,
            size_bytes=size,
            summary=f"{name} (dill pickle, {_human_size(size)}) -> {path}\n  {_PICKLE_NOTE}",
            path=path,
        )

    return ExportSummary(
        name=name,
        kind=kind,
        size_bytes=size,
        summary=f"{name} (unrecognized kind {kind!r}, {_human_size(size)}) -> {path}\n  written as opaque bytes; not decoded",
        path=path,
    )


def summarize_exports(exports: dict[str, Any], directory: Path, max_inline_images: int) -> list[ExportSummary]:
    """Write and describe every export, keeping the backend's ordering."""
    summaries: list[ExportSummary] = []
    images_left = max(0, max_inline_images)
    for name, artifact in exports.items():
        if not isinstance(artifact, dict):
            summaries.append(
                ExportSummary(name=name, kind="unknown", size_bytes=0, summary=f"{name}: unexpected artifact shape", failure="malformed artifact")
            )
            continue
        summary = summarize_export(name, artifact, directory, allow_image=images_left > 0)
        if summary.image is not None:
            images_left -= 1
        summaries.append(summary)
    return summaries


def excerpt_console(console_output: str, directory: Path) -> tuple[str, Path | None]:
    """Write the job's console log and return a context-safe excerpt plus its path."""
    if not console_output:
        return "(the job produced no console output)", None
    path = _artifact_path(directory, "console", ".txt")
    path.write_text(console_output, encoding="utf-8")
    excerpt = _excerpt(console_output, _MAX_INLINE_CONSOLE_CHARS, _CONSOLE_EXCERPT_SIDE_CHARS, f"console truncated; full log at {path}")
    return excerpt, path
