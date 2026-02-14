"""Shared models used across agents, tools, and memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Return a UTC ISO8601 timestamp string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Message:
    """Represents a conversation message stored in short-term memory."""

    role: str
    content: str
    timestamp: str = field(default_factory=utc_now_iso)


@dataclass(slots=True)
class LifecycleEvent:
    """Represents a streaming event emitted during an agent run."""

    stage: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)


@dataclass(slots=True)
class AgentRunResult:
    """Final output from an agent run."""

    agent: str
    task: str
    plan: Any
    action: Any
    observation: Any
    reflection: Any
    success: bool


@dataclass(slots=True)
class AgentMetrics:
    """Performance metrics collected per agent instance."""

    agent_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    tool_calls: int = 0
    total_runtime_seconds: float = 0.0
    last_error: str | None = None
    stage_timings: dict[str, float] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Compute success ratio in [0, 1]."""
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs
