"""Base exporter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

from cclog.models import ConversationRecord

ContentSelection = Literal["all", "messages", "tools", "thinking"]


@dataclass
class ExportConfig:
    """Configuration for export operations."""

    # What content to include
    content: ContentSelection = "all"

    # Max tokens for LLM export (approximate)
    max_tokens: int | None = None

    # Include thinking blocks
    include_thinking: bool = True

    # Include tool input/output
    include_tool_content: bool = True

    # Truncate long content
    truncate_length: int | None = None


class Exporter(ABC):
    """Base class for exporters."""

    def __init__(self, config: ExportConfig | None = None) -> None:
        self.config = config or ExportConfig()

    @abstractmethod
    def export(self, records: Iterator[ConversationRecord]) -> str:
        """Export records to string format.

        Args:
            records: Iterator of conversation records

        Returns:
            Formatted string output
        """
        ...

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name (e.g., 'markdown', 'csv')."""
        ...

    def _truncate(self, text: str, max_length: int | None = None) -> str:
        """Truncate text if needed."""
        length = max_length or self.config.truncate_length
        if length is None or len(text) <= length:
            return text
        return text[: length - 3] + "..."
