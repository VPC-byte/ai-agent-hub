"""Tool abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolResult:
    """Unified result object returned by tool executions."""

    success: bool
    output: Any
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all tools."""

    name: str
    description: str

    @abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult:
        """Execute a tool asynchronously."""

    def schema(self) -> dict[str, Any]:
        """Optional runtime schema metadata."""
        return {
            "name": self.name,
            "description": self.description,
        }
