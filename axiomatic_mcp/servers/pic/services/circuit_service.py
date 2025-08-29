import contextlib
import io
import json
from importlib.resources import files
from typing import Any, Optional

from ...constants.api_constants import ApiRoutes


class CircuitService:
    _instance: Optional["CircuitService"] = None

    @classmethod
    def get_instance(cls) -> "CircuitService":
        if cls._instance is None:
            cls._instance = CircuitService()
        return cls._instance

    async def get_netlist_from_code(self, current_file_content: str) -> dict:
        """
        Executes the given code + the get_netlist template in a sandboxed namespace,
        captures stdout, and parses the result as JSON.
        """
        if not current_file_content:
            raise ValueError("No code content provided.")

        # Load the template (from axiomatic_mcp/templates/get_netlist.template)
        template_code = files("axiomatic_mcp.templates").joinpath("get_netlist.template").read_text()

        # Merge user code + template
        full_code = f"{current_file_content.decode()}\n\n{template_code}"

        # Sandbox namespace
        namespace: dict[str, object] = {}

        # Capture stdout while executing code
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(full_code, namespace)

        stdout = buf.getvalue().strip()

        # Parse stdout as JSON
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse template output: {stdout}") from e

    async def generate_pic_circuit(self, body: dict) -> Any:
        return await self.api_client.post(ApiRoutes.REFINE_CIRCUIT, body)
