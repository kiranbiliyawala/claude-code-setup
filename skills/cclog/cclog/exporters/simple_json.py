"""Simple JSON exporter with flattened structure."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

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


class SimpleJsonExporter(Exporter):
    """Export conversation as simplified JSON.

    Produces a flattened structure optimized for parsing,
    without Pydantic model overhead.
    """

    def __init__(self, config: ExportConfig | None = None) -> None:
        super().__init__(config)

    @property
    def format_name(self) -> str:
        return "simple-json"

    def export(self, records: Iterator[ConversationRecord]) -> str:
        """Export records to simplified JSON format."""
        messages: list[dict[str, Any]] = []

        for record in records:
            if isinstance(record, UserRecord):
                messages.append(self._format_user_message(record))
            elif isinstance(record, AssistantRecord):
                messages.append(self._format_assistant_message(record))

        output: dict[str, Any] = {
            "message_count": len(messages),
            "messages": messages,
        }

        return json.dumps(output, indent=2, default=str)

    def _format_user_message(self, record: UserRecord) -> dict[str, Any]:
        """Format a user message."""
        message: dict[str, Any] = {
            "role": "user",
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
            "uuid": record.uuid,
        }

        text_parts: list[str] = []
        tool_results: list[dict[str, Any]] = []

        for block in record.message.get_content_blocks():
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
            elif isinstance(block, ToolResultBlock) and self.config.include_tool_content:
                tool_results.append(
                    {
                        "tool_use_id": block.tool_use_id,
                        "is_error": block.is_error,
                        "content": self._truncate(block.content_text),
                    }
                )

        if text_parts:
            message["text"] = "\n".join(text_parts)
        if tool_results:
            message["tool_results"] = tool_results

        return message

    def _format_assistant_message(self, record: AssistantRecord) -> dict[str, Any]:
        """Format an assistant message."""
        message: dict[str, Any] = {
            "role": "assistant",
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
            "uuid": record.uuid,
        }

        text_parts: list[str] = []
        thinking_parts: list[str] = []
        tool_uses: list[dict[str, Any]] = []

        for block in record.message.get_content_blocks():
            if isinstance(block, ThinkingBlock):
                if self.config.include_thinking:
                    thinking_parts.append(self._truncate(block.thinking))

            elif isinstance(block, TextBlock):
                text_parts.append(block.text)

            elif isinstance(block, ToolUseBlock) and self.config.include_tool_content:
                tool_use: dict[str, Any] = {
                    "id": block.id,
                    "name": block.name,
                }
                if block.name == "Task":
                    tool_use["description"] = block.description
                    tool_use["subagent_type"] = block.subagent_type
                else:
                    tool_use["input"] = block.input
                tool_uses.append(tool_use)

        if text_parts:
            message["text"] = "\n".join(text_parts)
        if thinking_parts:
            message["thinking"] = thinking_parts
        if tool_uses:
            message["tool_uses"] = tool_uses

        return message
