"""Research specialist agent."""

from __future__ import annotations

from typing import Any

from ai_agent_hub.core.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """Agent that gathers information from web search and cites sources."""

    async def plan(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "search_query": task,
            "max_results": 5,
            "strategy": "Search DuckDuckGo and synthesize concise findings with citations.",
        }

    async def act(self, plan: dict[str, Any]) -> dict[str, Any]:
        self.metrics_tracker.mark_tool_call()
        tool_result = await self.tool_registry.execute(
            "web_search",
            query=plan["search_query"],
            max_results=plan["max_results"],
        )

        if not tool_result.success:
            return {
                "findings": "Unable to retrieve web results.",
                "citations": [],
                "error": tool_result.error,
            }

        rows = tool_result.output or []
        findings_lines = [f"- {row.get('title', 'Untitled')}" for row in rows]
        citations = [row.get("url", "") for row in rows]
        findings = "\n".join(findings_lines) if findings_lines else "No results returned."

        await self.memory.add_knowledge(
            text=f"Research task: {plan['search_query']}\n{findings}",
            metadata={"agent": self.name, "task": plan["search_query"]},
        )

        return {
            "findings": findings,
            "citations": citations,
            "count": len(rows),
        }

    async def reflect(self, observation: Any) -> dict[str, Any]:
        action = observation.get("action", {}) if isinstance(observation, dict) else {}
        return {
            "summary": action.get("findings", "No findings available."),
            "citations": action.get("citations", []),
            "note": "Cite URLs when presenting externally.",
        }
