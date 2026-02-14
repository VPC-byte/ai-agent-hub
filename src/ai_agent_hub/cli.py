"""Typer-based CLI for AI Agent Hub."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from ai_agent_hub import create_default_hub

app = typer.Typer(help="AI Agent Hub CLI")


@app.command("list-tools")
def list_tools() -> None:
    """List registered built-in tools."""
    hub = create_default_hub()
    for tool in hub.tools.list_tools():
        typer.echo(f"- {tool['name']}: {tool['description']}")


@app.command("list-agents")
def list_agents() -> None:
    """List built-in agents."""
    hub = create_default_hub()
    for name, agent in hub.agents.items():
        typer.echo(f"- {name}: {agent.description}")


@app.command("run-agent")
def run_agent(
    agent: Annotated[str, typer.Option(help="Agent name: research|code|planner")],
    task: Annotated[str, typer.Option(help="Task to execute")],
    stream: Annotated[bool, typer.Option(help="Enable streaming output")] = False,
) -> None:
    """Run a single agent task."""

    async def _run() -> None:
        hub = create_default_hub()
        if stream:
            async for event in hub.stream_agent(agent, task):
                typer.echo(f"[{event.stage}] {event.message}")
            return

        result = await hub.run_agent(agent, task)
        typer.echo(json.dumps(asdict(result), indent=2, default=str))

    asyncio.run(_run())


@app.command("orchestrate")
def orchestrate(
    task: Annotated[str, typer.Option(help="Composite task to orchestrate")],
    stream: Annotated[bool, typer.Option(help="Enable streaming output")] = False,
) -> None:
    """Run planner-driven multi-agent orchestration."""

    async def _run() -> None:
        hub = create_default_hub()
        if stream:
            async for event in hub.stream_orchestration(task):
                typer.echo(f"[{event.stage}] {event.message}")
            return

        results = await hub.orchestrate(task)
        payload = [
            {"subtask": item.subtask, "agent": item.agent, "result": item.result.reflection}
            for item in results
        ]
        typer.echo(json.dumps(payload, indent=2, default=str))

    asyncio.run(_run())


@app.command("export-history")
def export_history(
    output: Annotated[Path, typer.Option(help="Output path")],
    fmt: Annotated[str, typer.Option(help="json|markdown")] = "json",
) -> None:
    """Export current conversation history."""
    hub = create_default_hub()
    hub.export_history(output, fmt)
    typer.echo(f"Exported history to {output}")


@app.command("metrics")
def metrics() -> None:
    """Show agent metrics snapshot."""

    async def _run() -> None:
        hub = create_default_hub()
        await hub.run_agent("planner", "example planning task")
        typer.echo(json.dumps(hub.metrics_snapshot(), indent=2, default=str))

    asyncio.run(_run())


if __name__ == "__main__":
    app()
