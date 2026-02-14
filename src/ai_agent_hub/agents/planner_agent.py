"""Planning and decomposition specialist agent."""

from __future__ import annotations

import re
from typing import Any

from ai_agent_hub.core.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """Agent that breaks complex objectives into sequenced subtasks."""

    async def plan(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        normalized = re.sub(r"\s+", " ", task).strip()
        raw_parts = re.split(r"\band\b|,|;", normalized, flags=re.IGNORECASE)
        parts = [part.strip() for part in raw_parts if part.strip()]
        if not parts:
            parts = [normalized]

        subtasks = [f"{idx + 1}. {part}" for idx, part in enumerate(parts)]
        return {
            "task": task,
            "subtasks": subtasks,
            "priority": "sequential",
        }

    async def act(self, plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "subtasks": [item.split(". ", 1)[1] if ". " in item else item for item in plan["subtasks"]],
            "priority": plan["priority"],
            "count": len(plan["subtasks"]),
        }

    async def reflect(self, observation: Any) -> dict[str, Any]:
        action = observation.get("action", {}) if isinstance(observation, dict) else {}
        return {
            "summary": f"Generated {action.get('count', 0)} subtasks for delegation.",
            "subtasks": action.get("subtasks", []),
        }
