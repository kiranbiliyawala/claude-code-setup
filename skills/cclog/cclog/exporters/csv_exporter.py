"""CSV exporter for tool calls."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator

from cclog.exporters.base import ExportConfig, Exporter
from cclog.models import (
    AssistantRecord,
    ConversationRecord,
    ToolResultBlock,
    ToolUseBlock,
    UserRecord,
)


class CsvExporter(Exporter):
    """Export tool calls as CSV."""

    def __init__(self, config: ExportConfig | None = None) -> None:
        super().__init__(config)

    @property
    def format_name(self) -> str:
        return "csv"

    def export(self, records: Iterator[ConversationRecord]) -> str:
        """Export tool calls to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "timestamp",
                "tool_name",
                "tool_use_id",
                "input_summary",
                "result_status",
                "result_summary",
            ]
        )

        # Collect tool_use blocks and match with results
        pending_tools: dict[str, tuple[str | None, str, str]] = {}

        for record in records:
            if isinstance(record, AssistantRecord):
                for block in record.message.get_content_blocks():
                    if isinstance(block, ToolUseBlock):
                        timestamp = record.timestamp.isoformat() if record.timestamp else ""
                        input_summary = self._summarize_input(block)
                        pending_tools[block.id] = (timestamp, block.name, input_summary)

            elif isinstance(record, UserRecord):
                for block in record.message.get_content_blocks():
                    if isinstance(block, ToolResultBlock) and block.tool_use_id in pending_tools:
                        timestamp, tool_name, input_summary = pending_tools.pop(block.tool_use_id)
                        result_status = "error" if block.is_error else "success"
                        result_summary = self._truncate(block.content_text, 200)

                        writer.writerow(
                            [
                                timestamp,
                                tool_name,
                                block.tool_use_id,
                                input_summary,
                                result_status,
                                result_summary,
                            ]
                        )

        return output.getvalue()

    def _summarize_input(self, block: ToolUseBlock) -> str:
        """Create a summary of tool input."""
        if block.name == "Task":
            desc = block.description or ""
            subagent_type = block.subagent_type or ""
            return f"{desc} ({subagent_type})" if subagent_type else desc

        # For other tools, create a brief JSON summary
        try:
            return self._truncate(json.dumps(block.input), 200)
        except (TypeError, ValueError):
            return str(block.input)[:200]
