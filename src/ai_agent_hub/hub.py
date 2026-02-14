"""High-level application facade for AI Agent Hub."""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator

from ai_agent_hub.agents import CodeAgent, PlannerAgent, ResearchAgent
from ai_agent_hub.config import HubConfig
from ai_agent_hub.core.memory import ChromaLongTermMemory, MemoryManager, ShortTermMemory
from ai_agent_hub.core.models import LifecycleEvent
from ai_agent_hub.core.orchestrator import DelegationResult, MultiAgentCoordinator
from ai_agent_hub.core.tool_registry import ToolRegistry
from ai_agent_hub.logging_config import setup_logging
from ai_agent_hub.tools import (
    APICallerTool,
    CalculatorTool,
    DuckDuckGoSearchTool,
    FileReaderTool,
    FileWriterTool,
    PythonExecutorTool,
)


class AgentHub:
    """Facade that exposes single-agent and multi-agent workflows."""

    def __init__(self, config: HubConfig | None = None) -> None:
        self.config = config or HubConfig.from_env()
        setup_logging(self.config.log_level)

        short_term = ShortTermMemory()
        long_term = ChromaLongTermMemory(persist_dir=self.config.memory_path)
        self.memory = MemoryManager(short_term=short_term, long_term=long_term)

        self.tools = ToolRegistry()
        self._register_default_tools(self.tools, self.config.workspace)

        self.research_agent = ResearchAgent(
            name="research",
            description="Web research specialist",
            tool_registry=self.tools,
            memory=self.memory,
        )
        self.code_agent = CodeAgent(
            name="code",
            description="Code implementation/review specialist",
            tool_registry=self.tools,
            memory=self.memory,
        )
        self.planner_agent = PlannerAgent(
            name="planner",
            description="Task decomposition specialist",
            tool_registry=self.tools,
            memory=self.memory,
        )

        self.agents = {
            "research": self.research_agent,
            "code": self.code_agent,
            "planner": self.planner_agent,
        }

        self.coordinator = MultiAgentCoordinator(
            planner=self.planner_agent,
            specialists={"research": self.research_agent, "code": self.code_agent},
        )

    @staticmethod
    def _register_default_tools(registry: ToolRegistry, workspace: Path) -> None:
        registry.register(DuckDuckGoSearchTool())
        registry.register(FileReaderTool(workspace=workspace))
        registry.register(FileWriterTool(workspace=workspace))
        registry.register(PythonExecutorTool())
        registry.register(CalculatorTool())
        registry.register(APICallerTool())

    async def run_agent(self, agent_name: str, task: str) -> Any:
        """Run one named built-in agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        return await self.agents[agent_name].run(task)

    async def stream_agent(self, agent_name: str, task: str) -> AsyncIterator[LifecycleEvent]:
        """Stream lifecycle events from a named agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        async for event in self.agents[agent_name].run_stream(task):
            yield event

    async def orchestrate(self, task: str) -> list[DelegationResult]:
        """Run multi-agent orchestration flow."""
        return await self.coordinator.run(task)

    async def stream_orchestration(self, task: str) -> AsyncIterator[LifecycleEvent]:
        """Stream multi-agent orchestration events."""
        async for event in self.coordinator.run_stream(task):
            yield event

    def export_history(self, output_path: Path, fmt: str = "json") -> None:
        """Export short-term conversation history."""
        self.memory.export_history(output_path=output_path, fmt=fmt)

    def metrics_snapshot(self) -> dict[str, dict[str, Any]]:
        """Return metrics for all built-in agents."""
        return {
            name: {
                "total_runs": agent.metrics.total_runs,
                "success_rate": agent.metrics.success_rate,
                "tool_calls": agent.metrics.tool_calls,
                "total_runtime_seconds": agent.metrics.total_runtime_seconds,
                "last_error": agent.metrics.last_error,
            }
            for name, agent in self.agents.items()
        }


def create_default_hub(config: HubConfig | None = None) -> AgentHub:
    """Factory helper to create fully configured hub instance."""
    return AgentHub(config=config)
