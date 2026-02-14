"""Abstract base class implementing the agent lifecycle."""

from __future__ import annotations

import abc
import logging
from typing import Any, AsyncIterator

from ai_agent_hub.core.memory import MemoryManager
from ai_agent_hub.core.metrics import MetricsTracker
from ai_agent_hub.core.models import AgentMetrics, AgentRunResult, LifecycleEvent
from ai_agent_hub.core.tool_registry import ToolRegistry


class BaseAgent(abc.ABC):
    """Defines lifecycle: init -> plan -> act -> observe -> reflect."""

    def __init__(
        self,
        name: str,
        description: str,
        tool_registry: ToolRegistry,
        memory: MemoryManager,
    ) -> None:
        self.name = name
        self.description = description
        self.tool_registry = tool_registry
        self.memory = memory
        self.logger = logging.getLogger(f"Agent.{name}")
        self.metrics_tracker = MetricsTracker(metrics=AgentMetrics(agent_name=name))

    async def initialize(self, task: str) -> dict[str, Any]:
        """Initialize runtime context before planning."""
        self.memory.add_message("system", f"{self.name} received task: {task}")
        return {"task": task}

    @abc.abstractmethod
    async def plan(self, task: str, context: dict[str, Any]) -> Any:
        """Create execution plan for the task."""

    @abc.abstractmethod
    async def act(self, plan: Any) -> Any:
        """Execute plan and produce action output."""

    async def observe(self, action: Any) -> Any:
        """Observe action outputs and store in memory."""
        self.memory.add_message("assistant", str(action))
        return {"action": action}

    async def reflect(self, observation: Any) -> Any:
        """Optional reflective step to produce final narrative response."""
        return {"summary": observation}

    async def run_stream(self, task: str) -> AsyncIterator[LifecycleEvent]:
        """Run full lifecycle while yielding streaming events."""
        self.metrics_tracker.start_run()
        success = False
        error_msg: str | None = None

        try:
            with self.metrics_tracker.stage("initialize"):
                context = await self.initialize(task)
            yield LifecycleEvent(stage="initialize", message="Initialized agent context", payload=context)

            with self.metrics_tracker.stage("plan"):
                plan = await self.plan(task, context)
            yield LifecycleEvent(stage="plan", message="Generated plan", payload={"plan": plan})

            with self.metrics_tracker.stage("act"):
                action = await self.act(plan)
            yield LifecycleEvent(stage="act", message="Executed actions", payload={"action": action})

            with self.metrics_tracker.stage("observe"):
                observation = await self.observe(action)
            yield LifecycleEvent(
                stage="observe",
                message="Captured observations",
                payload={"observation": observation},
            )

            with self.metrics_tracker.stage("reflect"):
                reflection = await self.reflect(observation)
            success = True
            yield LifecycleEvent(
                stage="reflect",
                message="Generated reflection",
                payload={"reflection": reflection},
            )

            yield LifecycleEvent(
                stage="complete",
                message="Run completed",
                payload={
                    "result": AgentRunResult(
                        agent=self.name,
                        task=task,
                        plan=plan,
                        action=action,
                        observation=observation,
                        reflection=reflection,
                        success=True,
                    )
                },
            )
        except Exception as exc:
            error_msg = str(exc)
            self.logger.exception("Agent run failed")
            yield LifecycleEvent(stage="error", message="Run failed", payload={"error": error_msg})
            raise
        finally:
            self.metrics_tracker.end_run(success=success, error=error_msg)

    async def run(self, task: str) -> AgentRunResult:
        """Run lifecycle and return final result object."""
        last_result: AgentRunResult | None = None
        async for event in self.run_stream(task):
            if event.stage == "complete":
                last_result = event.payload["result"]

        if last_result is None:
            raise RuntimeError("Agent run did not produce a final result")
        return last_result

    @property
    def metrics(self) -> AgentMetrics:
        """Return collected metrics for this agent."""
        return self.metrics_tracker.metrics
