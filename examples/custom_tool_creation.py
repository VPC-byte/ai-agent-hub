"""Example: register and use a custom tool."""

from __future__ import annotations

import asyncio
from typing import Any

from ai_agent_hub import create_default_hub
from ai_agent_hub.tools.base import BaseTool, ToolResult


class EchoTool(BaseTool):
    """Minimal custom tool for demonstration."""

    name = "echo"
    description = "Echo back input text"

    async def run(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, output={"echo": kwargs.get("text", "")})


async def main() -> None:
    hub = create_default_hub()
    hub.tools.register(EchoTool())
    result = await hub.tools.execute("echo", text="Custom tools are easy to add")
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
