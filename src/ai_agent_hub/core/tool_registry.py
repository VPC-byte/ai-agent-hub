"""Dynamic tool registration and execution."""

from __future__ import annotations

import logging
from typing import Any

from ai_agent_hub.exceptions import ToolExecutionError, ToolNotFoundError
from ai_agent_hub.tools.base import BaseTool, ToolResult


class ToolRegistry:
    """Registry for dynamic tool registration, discovery, and execution."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._logger = logging.getLogger(self.__class__.__name__)

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance by its unique name."""
        if tool.name in self._tools:
            self._logger.warning("Replacing tool '%s'", tool.name)
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Remove a tool from the registry."""
        self._tools.pop(tool_name, None)

    def get(self, tool_name: str) -> BaseTool:
        """Return a tool or raise if not found."""
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolNotFoundError(f"Tool not found: {tool_name}")
        return tool

    def list_tools(self) -> list[dict[str, Any]]:
        """List registered tool metadata."""
        return [tool.schema() for tool in self._tools.values()]

    async def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Execute a named tool with keyword arguments."""
        tool = self.get(tool_name)
        try:
            return await tool.run(**kwargs)
        except Exception as exc:  # pragma: no cover - defensive envelope
            raise ToolExecutionError(f"Tool '{tool_name}' failed: {exc}") from exc
