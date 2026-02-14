"""Code specialist agent."""

from __future__ import annotations

from typing import Any

from ai_agent_hub.core.base_agent import BaseAgent


class CodeAgent(BaseAgent):
    """Agent focused on writing, reviewing, and debugging Python code tasks."""

    async def plan(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        lower = task.lower()
        mode = "implement"
        if "review" in lower:
            mode = "review"
        elif "debug" in lower or "fix" in lower:
            mode = "debug"
        return {
            "mode": mode,
            "task": task,
            "steps": [
                "Understand objective",
                "Produce code guidance",
                "Optionally validate snippet in sandbox",
            ],
        }

    async def act(self, plan: dict[str, Any]) -> dict[str, Any]:
        mode = plan["mode"]
        task = plan["task"]

        if mode == "review":
            return {
                "mode": mode,
                "output": (
                    "Code review checklist: correctness, edge cases, readability, "
                    "tests, and security-sensitive operations."
                ),
            }

        if mode == "debug":
            snippet = "x = 1\nprint(x)"
            self.metrics_tracker.mark_tool_call()
            exec_result = await self.tool_registry.execute("python_executor", code=snippet, timeout=2)
            return {
                "mode": mode,
                "output": "Debug strategy: reproduce, isolate, patch, and verify with tests.",
                "sandbox": exec_result.output if exec_result.success else exec_result.error,
            }

        generated = (
            "def solve_task(input_data):\n"
            "    \"\"\"Generated starter implementation.\"\"\"\n"
            "    return input_data\n"
        )
        self.metrics_tracker.mark_tool_call()
        write_result = await self.tool_registry.execute(
            "file_writer",
            path="generated_solution.py",
            content=generated,
            append=False,
        )

        return {
            "mode": mode,
            "output": generated,
            "artifact": write_result.output if write_result.success else write_result.error,
            "task": task,
        }

    async def reflect(self, observation: Any) -> dict[str, Any]:
        action = observation.get("action", {}) if isinstance(observation, dict) else {}
        return {
            "next_steps": [
                "Add input validation",
                "Write unit tests",
                "Run formatter and linter",
            ],
            "mode": action.get("mode", "unknown"),
        }
