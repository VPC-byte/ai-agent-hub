from __future__ import annotations

import pytest

from ai_agent_hub import AgentHub
from ai_agent_hub.config import HubConfig
from ai_agent_hub.tools.base import BaseTool, ToolResult


class FakeSearchTool(BaseTool):
    name = "web_search"
    description = "fake search"

    async def run(self, **kwargs):
        return ToolResult(
            success=True,
            output=[
                {"title": "Async Python", "url": "https://example.com/async"},
                {"title": "Agent Design", "url": "https://example.com/agents"},
            ],
        )


@pytest.fixture
def hub(tmp_path):
    config = HubConfig(memory_path=tmp_path / "memory", workspace=tmp_path)
    return AgentHub(config=config)


@pytest.mark.asyncio
async def test_planner_agent_run(hub: AgentHub) -> None:
    result = await hub.run_agent("planner", "Research APIs and write starter code")
    assert result.success is True
    assert isinstance(result.action, dict)
    assert result.action["count"] >= 1


@pytest.mark.asyncio
async def test_research_agent_uses_citations(hub: AgentHub) -> None:
    hub.tools.register(FakeSearchTool())
    result = await hub.run_agent("research", "best testing libraries")
    assert result.success is True
    assert len(result.action["citations"]) == 2


@pytest.mark.asyncio
async def test_code_agent_generates_file(hub: AgentHub) -> None:
    result = await hub.run_agent("code", "implement a parser")
    assert result.success is True
    generated = hub.config.workspace / "generated_solution.py"
    assert generated.exists()


@pytest.mark.asyncio
async def test_multi_agent_orchestration(hub: AgentHub) -> None:
    hub.tools.register(FakeSearchTool())
    results = await hub.orchestrate("Research CI best practices and implement Python template")
    assert len(results) >= 2
    assert {row.agent for row in results}.issubset({"research", "code"})


@pytest.mark.asyncio
async def test_streaming_events_and_metrics(hub: AgentHub) -> None:
    events = [event async for event in hub.stream_agent("planner", "Plan this")]
    stages = [event.stage for event in events]
    assert "initialize" in stages
    assert "complete" in stages

    snapshot = hub.metrics_snapshot()
    assert snapshot["planner"]["total_runs"] >= 1
