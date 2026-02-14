"""Metric collection utilities."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

from ai_agent_hub.core.models import AgentMetrics


@dataclass(slots=True)
class MetricsTracker:
    """Tracks timing and success metrics for agent runs."""

    metrics: AgentMetrics
    _run_start: float | None = field(default=None, init=False)

    def start_run(self) -> None:
        """Mark run start."""
        self.metrics.total_runs += 1
        self._run_start = time.perf_counter()

    def end_run(self, success: bool, error: str | None = None) -> None:
        """Finalize run metrics."""
        if success:
            self.metrics.successful_runs += 1
        else:
            self.metrics.failed_runs += 1
            self.metrics.last_error = error

        if self._run_start is not None:
            self.metrics.total_runtime_seconds += time.perf_counter() - self._run_start
            self._run_start = None

    @contextmanager
    def stage(self, stage_name: str) -> Iterator[None]:
        """Track runtime for a lifecycle stage."""
        start = time.perf_counter()
        try:
            yield
        finally:
            self.metrics.stage_timings[stage_name] = (
                self.metrics.stage_timings.get(stage_name, 0.0) + (time.perf_counter() - start)
            )

    def mark_tool_call(self) -> None:
        """Increment tool call count."""
        self.metrics.tool_calls += 1
