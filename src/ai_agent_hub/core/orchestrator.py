"""Multi-agent orchestration primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator

from ai_agent_hub.agents.planner_agent import PlannerAgent
from ai_agent_hub.core.base_agent import BaseAgent
from ai_agent_hub.core.models import LifecycleEvent


@dataclass(slots=True)
class DelegationResult:
    """Result from one delegated subtask."""

    subtask: str
    agent: str
    result: Any


class MultiAgentCoordinator:
    """Coordinates planner + specialist agents for composite tasks."""

    def __init__(self, planner: PlannerAgent, specialists: dict[str, BaseAgent]) -> None:
        self.planner = planner
        self.specialists = specialists

    def _choose_agent(self, subtask: str) -> BaseAgent:
        lower = subtask.lower()
        if any(token in lower for token in ("code", "debug", "implement", "python", "test")):
            return self.specialists["code"]
        return self.specialists["research"]

    async def run_stream(self, task: str) -> AsyncIterator[LifecycleEvent]:
        """Run orchestration and emit stream events for planner and delegates."""
        planner_output = await self.planner.run(task)
        plan = planner_output.action
        subtasks = plan.get("subtasks", []) if isinstance(plan, dict) else []

        yield LifecycleEvent(
            stage="orchestrator_plan",
            message="Planner generated subtasks",
            payload={"subtasks": subtasks},
        )

        results: list[DelegationResult] = []
        for subtask in subtasks:
            agent = self._choose_agent(subtask)
            delegated_result = await agent.run(subtask)
            result = DelegationResult(subtask=subtask, agent=agent.name, result=delegated_result)
            results.append(result)
            yield LifecycleEvent(
                stage="delegation",
                message=f"Delegated subtask to {agent.name}",
                payload={"delegation": result},
            )

        yield LifecycleEvent(
            stage="orchestrator_complete",
            message="Multi-agent execution complete",
            payload={"results": results},
        )

    async def run(self, task: str) -> list[DelegationResult]:
        """Run orchestration and collect delegation results."""
        final_results: list[DelegationResult] = []
        async for event in self.run_stream(task):
            if event.stage == "orchestrator_complete":
                final_results = event.payload["results"]
        return final_results
