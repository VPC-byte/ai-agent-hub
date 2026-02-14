"""AI Agent Hub: modular, extensible multi-agent framework."""

from ai_agent_hub.config import HubConfig
from ai_agent_hub.hub import AgentHub, create_default_hub

__all__ = ["AgentHub", "HubConfig", "create_default_hub"]
__version__ = "0.1.0"
