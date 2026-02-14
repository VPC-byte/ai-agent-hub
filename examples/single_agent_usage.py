"""Example: run a single built-in agent."""

from __future__ import annotations

import asyncio

from ai_agent_hub import create_default_hub


async def main() -> None:
    hub = create_default_hub()
    result = await hub.run_agent("planner", "Research vector databases and build a demo")
    print(result.reflection)


if __name__ == "__main__":
    asyncio.run(main())
