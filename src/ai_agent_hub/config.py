"""Configuration primitives for AI Agent Hub."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class HubConfig:
    """Runtime configuration loaded from environment variables.

    Environment variables:
    - `AI_AGENT_HUB_LOG_LEVEL`
    - `AI_AGENT_HUB_MEMORY_PATH`
    - `AI_AGENT_HUB_DEFAULT_TIMEOUT`
    - `AI_AGENT_HUB_WORKSPACE`
    """

    log_level: str = "INFO"
    memory_path: Path = Path(".agent_memory")
    default_timeout: int = 15
    workspace: Path = Path(".")

    @classmethod
    def from_env(cls) -> "HubConfig":
        """Build a config object from environment variables."""
        return cls(
            log_level=os.getenv("AI_AGENT_HUB_LOG_LEVEL", "INFO"),
            memory_path=Path(os.getenv("AI_AGENT_HUB_MEMORY_PATH", ".agent_memory")),
            default_timeout=int(os.getenv("AI_AGENT_HUB_DEFAULT_TIMEOUT", "15")),
            workspace=Path(os.getenv("AI_AGENT_HUB_WORKSPACE", ".")),
        )
