import asyncio
import json
import tempfile
from contextlib import suppress
from importlib.resources import files
from pathlib import Path
from typing import Any, Optional

from ...constants.api_constants import ApiRoutes

# Import API ROUTES
from .axiomatic_api_client import AxiomaticApiClient


class CircuitService:
    _instance: Optional["CircuitService"] = None

    def __init__(self) -> None:
        self.api_client = AxiomaticApiClient.get_instance()

    @classmethod
    def get_instance(cls) -> "CircuitService":
        if cls._instance is None:
            cls._instance = CircuitService()
        return cls._instance

    async def get_netlist_from_code(self, current_file_content: str | None) -> Any:
        if not current_file_content:
            raise ValueError("No code content available.")

        python_path = await self.setup_environment_service.get_python_interpreter_path()
        if not python_path:
            raise ValueError("Interpreter path is undefined.")

        # Load the template
        template_code = files("axiomatic_mcp.templates").joinpath("get_netlist.template").read_text()

        full_code = f"{current_file_content}\n\n{template_code}"

        # Create a temp file for execution
        with tempfile.NamedTemporaryFile("w+", suffix=".py", delete=False) as tmp_file:
            temp_path = Path(tmp_file.name)
            tmp_file.write(full_code)

        try:
            process = await asyncio.create_subprocess_exec(
                python_path,
                str(temp_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(stderr_bytes.decode().strip())

            stdout = stdout_bytes.decode().strip()
        finally:
            with suppress(Exception):
                temp_path.unlink(missing_ok=True)

        try:
            parsed_output = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Python output: {e}") from e

        if "__error__" in parsed_output:
            raise RuntimeError(f"Python error: {parsed_output['__error__']}")

        return parsed_output

    async def generate_pic_circuit(self, body: dict) -> Any:
        return await self.api_client.post(ApiRoutes.REFINE_CIRCUIT, body)
