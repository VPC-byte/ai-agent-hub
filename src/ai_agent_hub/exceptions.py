"""Custom exceptions for AI Agent Hub."""


class AgentHubError(Exception):
    """Base exception for all framework errors."""


class ToolNotFoundError(AgentHubError):
    """Raised when a tool cannot be found in the registry."""


class ToolExecutionError(AgentHubError):
    """Raised when tool execution fails."""


class MemoryError(AgentHubError):
    """Raised when memory operations fail."""
