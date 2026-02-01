"""Full-text search across conversation content."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from cclog.models import (
    AssistantRecord,
    ConversationRecord,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserRecord,
)

SearchScope = Literal["text", "thinking", "tool_input", "tool_result", "all"]


@dataclass
class SearchFilter:
    """Filter criteria for search.

    All filters are optional. Pattern is required.
    """

    pattern: str
    scope: SearchScope = "all"
    regex: bool = False
    case_insensitive: bool = False
    context_lines: int = 0

    # Pagination
    limit: int | None = None
    offset: int = 0


@dataclass
class SearchMatch:
    """A single search match with context.

    Contains the matched text, location information, and surrounding context.
    """

    # Location
    message_uuid: str | None
    timestamp: datetime | None
    role: str
    scope: str  # Which scope this match was found in

    # Match details
    line_number: int  # Line within the content block
    match_text: str  # The matched portion
    line_text: str  # Full line containing match

    # Context
    context_before: list[str] = field(default_factory=lambda: [])
    context_after: list[str] = field(default_factory=lambda: [])

    # Block metadata
    block_type: str | None = None
    tool_name: str | None = None  # For tool_use/tool_result
    tool_use_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON output."""
        result: dict[str, Any] = {
            "message_uuid": self.message_uuid,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "role": self.role,
            "scope": self.scope,
            "line_number": self.line_number,
            "match_text": self.match_text,
            "line_text": self.line_text,
        }

        if self.context_before:
            result["context_before"] = self.context_before
        if self.context_after:
            result["context_after"] = self.context_after
        if self.tool_name:
            result["tool_name"] = self.tool_name
        if self.tool_use_id:
            result["tool_use_id"] = self.tool_use_id

        return result


def _compile_pattern(filter_: SearchFilter) -> re.Pattern[str]:
    """Compile search pattern to regex."""
    # Escape special regex characters for literal search unless regex mode
    pattern = filter_.pattern if filter_.regex else re.escape(filter_.pattern)
    flags = re.IGNORECASE if filter_.case_insensitive else 0
    return re.compile(pattern, flags)


def _search_text(
    text: str,
    pattern: re.Pattern[str],
    context_lines: int,
) -> Iterator[tuple[int, str, str, list[str], list[str]]]:
    """Search text and yield matches with context.

    Yields:
        (line_number, match_text, line_text, context_before, context_after)
    """
    lines = text.split("\n")

    for i, line in enumerate(lines):
        match = pattern.search(line)
        if match:
            # Extract context
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)

            context_before = lines[start:i] if context_lines > 0 else []
            context_after = lines[i + 1 : end] if context_lines > 0 else []

            yield (i + 1, match.group(), line, context_before, context_after)


def _search_block(
    block: TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock,
    pattern: re.Pattern[str],
    filter_: SearchFilter,
    role: str,
    message_uuid: str | None,
    timestamp: datetime | None,
) -> Iterator[SearchMatch]:
    """Search a single content block."""
    scope = filter_.scope
    context_lines = filter_.context_lines

    # Determine if we should search this block
    if isinstance(block, TextBlock):
        if scope not in ("text", "all"):
            return
        search_text = block.text
        block_scope = "text"
        tool_name = None
        tool_use_id = None

    elif isinstance(block, ThinkingBlock):
        if scope not in ("thinking", "all"):
            return
        search_text = block.thinking
        block_scope = "thinking"
        tool_name = None
        tool_use_id = None

    elif isinstance(block, ToolUseBlock):
        if scope not in ("tool_input", "all"):
            return
        # Search in the serialized input
        import json

        search_text = json.dumps(block.input, indent=2)
        block_scope = "tool_input"
        tool_name = block.name
        tool_use_id = block.id

    else:
        # ToolResultBlock
        if scope not in ("tool_result", "all"):
            return
        search_text = block.content_text
        block_scope = "tool_result"
        tool_name = None
        tool_use_id = block.tool_use_id

    # Search and yield matches
    for line_num, match_text, line_text, ctx_before, ctx_after in _search_text(
        search_text, pattern, context_lines
    ):
        yield SearchMatch(
            message_uuid=message_uuid,
            timestamp=timestamp,
            role=role,
            scope=block_scope,
            line_number=line_num,
            match_text=match_text,
            line_text=line_text,
            context_before=ctx_before,
            context_after=ctx_after,
            block_type=block.type,
            tool_name=tool_name,
            tool_use_id=tool_use_id,
        )


def search_content(
    records: Iterator[ConversationRecord],
    filter_: SearchFilter,
) -> Iterator[SearchMatch]:
    """Search across conversation content.

    Args:
        records: Iterator of conversation records
        filter_: Search filter criteria

    Yields:
        SearchMatch for each match found
    """
    pattern = _compile_pattern(filter_)
    count = 0
    yielded = 0

    for record in records:
        if not isinstance(record, (UserRecord, AssistantRecord)):
            continue

        role = "user" if isinstance(record, UserRecord) else "assistant"

        for block in record.message.get_content_blocks():
            for match in _search_block(
                block,
                pattern,
                filter_,
                role,
                record.uuid,
                record.timestamp,
            ):
                count += 1

                if count <= filter_.offset:
                    continue

                yield match
                yielded += 1

                if filter_.limit is not None and yielded >= filter_.limit:
                    return
