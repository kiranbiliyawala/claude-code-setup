"""Markdown exporter for human-readable conversation export."""

from __future__ import annotations

from collections.abc import Iterator

from cclog.exporters.base import ExportConfig, Exporter
from cclog.models import (
    AssistantRecord,
    ConversationRecord,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserRecord,
)


class MarkdownExporter(Exporter):
    """Export conversation as Markdown."""

    def __init__(self, config: ExportConfig | None = None) -> None:
        super().__init__(config)

    @property
    def format_name(self) -> str:
        return "markdown"

    def export(self, records: Iterator[ConversationRecord]) -> str:
        """Export records to Markdown format."""
        lines: list[str] = []
        lines.append("# Conversation Export\n")

        for record in records:
            if isinstance(record, UserRecord):
                lines.extend(self._format_user_message(record))
            elif isinstance(record, AssistantRecord):
                lines.extend(self._format_assistant_message(record))

        return "\n".join(lines)

    def _format_user_message(self, record: UserRecord) -> list[str]:
        """Format a user message."""
        lines: list[str] = []

        # Header with timestamp
        timestamp = record.timestamp.isoformat() if record.timestamp else "unknown"
        lines.append(f"## User ({timestamp})\n")

        for block in record.message.get_content_blocks():
            if isinstance(block, TextBlock):
                lines.append(block.text)
                lines.append("")
            elif isinstance(block, ToolResultBlock):
                if self.config.include_tool_content:
                    lines.append(f"**Tool Result** (`{block.tool_use_id}`)")
                    if block.is_error:
                        lines.append("*Error:*")
                    lines.append("```")
                    lines.append(self._truncate(block.content_text))
                    lines.append("```")
                    lines.append("")

        return lines

    def _format_assistant_message(self, record: AssistantRecord) -> list[str]:
        """Format an assistant message."""
        lines: list[str] = []

        # Header with timestamp
        timestamp = record.timestamp.isoformat() if record.timestamp else "unknown"
        lines.append(f"## Assistant ({timestamp})\n")

        for block in record.message.get_content_blocks():
            if isinstance(block, ThinkingBlock):
                if self.config.include_thinking:
                    lines.append("<details>")
                    lines.append("<summary>Thinking</summary>\n")
                    lines.append(self._truncate(block.thinking))
                    lines.append("")
                    lines.append("</details>\n")

            elif isinstance(block, TextBlock):
                lines.append(block.text)
                lines.append("")

            elif isinstance(block, ToolUseBlock) and self.config.include_tool_content:
                lines.append(f"**Tool Use: {block.name}** (`{block.id}`)")

                # Special handling for Task tool
                if block.name == "Task" and block.description:
                    lines.append(f"*{block.description}*")

                lines.append("```json")
                import json

                input_str = json.dumps(block.input, indent=2)
                lines.append(self._truncate(input_str, 500))
                lines.append("```")
                lines.append("")

        return lines
