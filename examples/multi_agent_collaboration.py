"""Example: run planner-driven multi-agent delegation."""

from __future__ import annotations

import asyncio

from ai_agent_hub import create_default_hub


async def main() -> None:
    hub = create_default_hub()
    task = "Research web scraping best practices and implement a Python starter template"

    async for event in hub.stream_orchestration(task):
        print(f"[{event.stage}] {event.message}")


if __name__ == "__main__":
    asyncio.run(main())
