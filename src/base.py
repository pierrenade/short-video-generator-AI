"""Base class for agent tools.

Each tool knows how to describe itself to the model (via `to_schema()`)
and how to execute itself given a dict of validated inputs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class ToolError(Exception):
    """Raised when a tool cannot complete its work. The message is
    shown to the model as a tool_result with is_error=True."""


@dataclass
class ToolResult:
    """Output of a successful tool invocation."""

    content: str
    is_error: bool = False


class Tool(ABC):
    """Abstract base class for all tools."""

    name: str
    description: str
    input_schema: dict[str, Any]

    def to_schema(self) -> dict[str, Any]:
        """Serialize to the dict shape the Anthropic API expects."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool. Raise ToolError on failure."""
        raise NotImplementedError
