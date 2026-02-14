from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("typer")
from typer.testing import CliRunner

from ai_agent_hub.cli import app


runner = CliRunner()


def test_list_agents_command() -> None:
    result = runner.invoke(app, ["list-agents"])
    assert result.exit_code == 0
    assert "research" in result.stdout
    assert "planner" in result.stdout


def test_run_agent_streaming_command() -> None:
    result = runner.invoke(
        app,
        ["run-agent", "--agent", "planner", "--task", "plan this", "--stream"],
    )
    assert result.exit_code == 0
    assert "[initialize]" in result.stdout


def test_export_history_command(tmp_path: Path) -> None:
    out = tmp_path / "history.json"
    result = runner.invoke(app, ["export-history", "--output", str(out), "--fmt", "json"])
    assert result.exit_code == 0
    assert out.exists()
