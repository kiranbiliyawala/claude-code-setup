"""LLM-optimized exporter with token budget."""

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

# Approximate chars per token (conservative estimate)
CHARS_PER_TOKEN = 4


class LlmExporter(Exporter):
    """Export conversation optimized for LLM context windows.

    Produces a token-efficient summary that fits within budget.
    Prioritizes: user messages > assistant text > tool calls > thinking.
    """

    def __init__(self, config: ExportConfig | None = None) -> None:
        super().__init__(config)
        self.max_chars = (
            (config.max_tokens * CHARS_PER_TOKEN) if config and config.max_tokens else None
        )

    @property
    def format_name(self) -> str:
        return "llm"

    def export(self, records: Iterator[ConversationRecord]) -> str:
        """Export records with token budget awareness."""
        # First pass: collect all content
        messages: list[tuple[str, str, list[str]]] = []  # (role, timestamp, content_parts)

        for record in records:
            if isinstance(record, UserRecord):
                timestamp = record.timestamp.isoformat() if record.timestamp else ""
                parts = self._extract_user_parts(record)
                if parts:
                    messages.append(("user", timestamp, parts))

            elif isinstance(record, AssistantRecord):
                timestamp = record.timestamp.isoformat() if record.timestamp else ""
                parts = self._extract_assistant_parts(record)
                if parts:
                    messages.append(("assistant", timestamp, parts))

        # Build output with budget awareness
        lines: list[str] = []
        current_chars = 0

        for role, timestamp, parts in messages:
            # Format message header
            header = f"[{role.upper()}] {timestamp}"

            # Calculate size of this message
            message_lines = [header]
            message_lines.extend(parts)
            message_lines.append("")  # blank line between messages

            message_text = "\n".join(message_lines)
            message_chars = len(message_text)

            # Check budget
            if self.max_chars and current_chars + message_chars > self.max_chars:
                # Try to fit a truncated version
                remaining = self.max_chars - current_chars - len(header) - 50
                if remaining > 100:
                    truncated = self._truncate_parts(parts, remaining)
                    lines.append(header)
                    lines.extend(truncated)
                    lines.append("[... truncated ...]")
                    lines.append("")
                break

            lines.extend(message_lines)
            current_chars += message_chars

        return "\n".join(lines)

    def _extract_user_parts(self, record: UserRecord) -> list[str]:
        """Extract content parts from user message."""
        parts: list[str] = []

        for block in record.message.get_content_blocks():
            if isinstance(block, TextBlock):
                parts.append(block.text)
            elif isinstance(block, ToolResultBlock) and self.config.include_tool_content:
                status = "[ERROR]" if block.is_error else "[OK]"
                content = self._truncate(block.content_text, 500)
                parts.append(f"Tool result {status}: {content}")

        return parts

    def _extract_assistant_parts(self, record: AssistantRecord) -> list[str]:
        """Extract content parts from assistant message."""
        parts: list[str] = []

        for block in record.message.get_content_blocks():
            if isinstance(block, ThinkingBlock):
                if self.config.include_thinking:
                    # Heavily truncate thinking for LLM export
                    thinking = self._truncate(block.thinking, 200)
                    parts.append(f"<thinking>{thinking}</thinking>")

            elif isinstance(block, TextBlock):
                parts.append(block.text)

            elif isinstance(block, ToolUseBlock) and self.config.include_tool_content:
                # Compact tool representation
                if block.name == "Task":
                    desc = block.description or "no description"
                    parts.append(f"[Tool: Task] {desc}")
                else:
                    parts.append(f"[Tool: {block.name}]")

        return parts

    def _truncate_parts(self, parts: list[str], max_chars: int) -> list[str]:
        """Truncate parts to fit within character budget."""
        result: list[str] = []
        remaining = max_chars

        for part in parts:
            if remaining <= 0:
                break
            if len(part) <= remaining:
                result.append(part)
                remaining -= len(part) + 1  # +1 for newline
            else:
                result.append(part[:remaining] + "...")
                break

        return result
