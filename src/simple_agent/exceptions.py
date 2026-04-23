class AgentError(Exception):
    """Base exception for all agent errors."""


class LLMError(AgentError):
    """Error calling the LLM API."""


class ToolError(AgentError):
    """Error executing a tool."""


class ResponseParseError(AgentError):
    """Error parsing the LLM response."""
