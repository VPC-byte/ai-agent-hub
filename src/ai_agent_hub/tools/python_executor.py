"""Sandboxed Python execution tool."""

from __future__ import annotations

import asyncio
import builtins
import contextlib
import io
from typing import Any

from ai_agent_hub.tools.base import BaseTool, ToolResult


class PythonExecutorTool(BaseTool):
    """Execute Python code with restricted globals and timeout."""

    name = "python_executor"
    description = "Execute Python snippets in a restricted sandbox"

    _ALLOWED_BUILTINS = {
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "enumerate",
        "float",
        "int",
        "len",
        "list",
        "max",
        "min",
        "pow",
        "print",
        "range",
        "reversed",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "zip",
    }

    def _execute_sync(self, code: str) -> dict[str, Any]:
        safe_builtins = {name: getattr(builtins, name) for name in self._ALLOWED_BUILTINS}
        safe_globals: dict[str, Any] = {
            "__builtins__": safe_builtins,
            "math": __import__("math"),
        }
        safe_locals: dict[str, Any] = {}

        # Disallow import statements in user code for sandbox safety.
        if "import " in code or "__import__" in code:
            raise ValueError("Import statements are not allowed in sandbox mode")

        stdout_buffer = io.StringIO()
        with contextlib.redirect_stdout(stdout_buffer):
            exec(code, safe_globals, safe_locals)  # noqa: S102 - intentionally sandboxed exec

        return {
            "stdout": stdout_buffer.getvalue(),
            "locals": {k: v for k, v in safe_locals.items() if not k.startswith("_")},
        }

    async def run(self, **kwargs: Any) -> ToolResult:
        code = kwargs.get("code")
        timeout_seconds = float(kwargs.get("timeout", 3.0))
        if not code:
            return ToolResult(success=False, output=None, error="Missing 'code'")

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self._execute_sync, str(code)),
                timeout=timeout_seconds,
            )
            return ToolResult(success=True, output=result)
        except Exception as exc:
            return ToolResult(success=False, output=None, error=str(exc))
