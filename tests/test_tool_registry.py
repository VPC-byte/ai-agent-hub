from __future__ import annotations

import pytest

from ai_agent_hub.core.tool_registry import ToolRegistry
from ai_agent_hub.exceptions import ToolNotFoundError
from ai_agent_hub.tools.base import BaseTool, ToolResult


class DummyTool(BaseTool):
    name = "dummy"
    description = "dummy tool"

    async def run(self, **kwargs):
        return ToolResult(success=True, output={"echo": kwargs.get("value")})


@pytest.mark.asyncio
async def test_register_list_and_execute_tool() -> None:
    registry = ToolRegistry()
    registry.register(DummyTool())

    names = [row["name"] for row in registry.list_tools()]
    assert "dummy" in names

    result = await registry.execute("dummy", value=42)
    assert result.success is True
    assert result.output["echo"] == 42


def test_get_missing_tool_raises() -> None:
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError):
        registry.get("missing")


def test_unregister_tool() -> None:
    registry = ToolRegistry()
    registry.register(DummyTool())
    registry.unregister("dummy")

    with pytest.raises(ToolNotFoundError):
        registry.get("dummy")
