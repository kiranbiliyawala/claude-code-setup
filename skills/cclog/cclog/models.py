"""Pydantic models for Claude Code JSONL conversation records."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


# Content block types
class ThinkingBlock(BaseModel):
    """Internal reasoning block."""

    type: Literal["thinking"] = "thinking"
    thinking: str


class TextBlock(BaseModel):
    """Response text block."""

    type: Literal["text"] = "text"
    text: str


class ToolUseBlock(BaseModel):
    """Tool invocation block."""

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any]

    @property
    def description(self) -> str | None:
        """Get Task description if this is a Task tool."""
        if self.name == "Task":
            return self.input.get("description")
        return None

    @property
    def subagent_type(self) -> str | None:
        """Get subagent type if this is a Task tool."""
        if self.name == "Task":
            return self.input.get("subagent_type")
        return None


class ToolResultBlock(BaseModel):
    """Tool output block."""

    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str | list[dict[str, Any]]
    is_error: bool = False

    @property
    def content_text(self) -> str:
        """Extract text content regardless of format."""
        if isinstance(self.content, str):
            return self.content
        # Content is a list of dicts with type/text fields
        texts: list[str] = []
        for item in self.content:
            if "text" in item:
                texts.append(str(item["text"]))
        return "\n".join(texts)


ContentBlock = Annotated[
    ThinkingBlock | TextBlock | ToolUseBlock | ToolResultBlock,
    Field(discriminator="type"),
]


# Message types
class Message(BaseModel):
    """Base message structure."""

    role: Literal["user", "assistant"]
    content: str | list[ContentBlock]

    def get_content_blocks(self) -> list[ContentBlock]:
        """Get content as list of blocks."""
        if isinstance(self.content, str):
            return [TextBlock(text=self.content)]
        return self.content

    def get_tool_uses(self) -> list[ToolUseBlock]:
        """Extract all tool_use blocks."""
        return [b for b in self.get_content_blocks() if isinstance(b, ToolUseBlock)]

    def get_tool_results(self) -> list[ToolResultBlock]:
        """Extract all tool_result blocks."""
        return [b for b in self.get_content_blocks() if isinstance(b, ToolResultBlock)]


# Record types
class BaseRecord(BaseModel):
    """Base conversation record."""

    type: str
    uuid: str | None = None
    timestamp: datetime | None = None
    session_id: str | None = Field(None, alias="sessionId")
    parent_uuid: str | None = Field(None, alias="parentUuid")
    cwd: str | None = None
    git_branch: str | None = Field(None, alias="gitBranch")
    version: str | None = None

    model_config = {"populate_by_name": True}


class UserRecord(BaseRecord):
    """User message record."""

    type: Literal["user"] = "user"  # pyright: ignore[reportIncompatibleVariableOverride]
    message: Message


class AssistantRecord(BaseRecord):
    """Assistant message record."""

    type: Literal["assistant"] = "assistant"  # pyright: ignore[reportIncompatibleVariableOverride]
    message: Message
    request_id: str | None = Field(None, alias="requestId")


class SystemRecord(BaseRecord):
    """System message record."""

    type: Literal["system"] = "system"  # pyright: ignore[reportIncompatibleVariableOverride]
    message: Message | None = None


class FileHistorySnapshot(BaseRecord):
    """File history snapshot record."""

    type: Literal["file-history-snapshot"] = "file-history-snapshot"  # pyright: ignore[reportIncompatibleVariableOverride]
    message_id: str | None = Field(None, alias="messageId")
    snapshot: dict[str, Any] | None = None
    is_snapshot_update: bool = Field(False, alias="isSnapshotUpdate")


ConversationRecord = UserRecord | AssistantRecord | SystemRecord | FileHistorySnapshot


def parse_record(data: dict[str, Any]) -> ConversationRecord:
    """Parse a raw dict into the appropriate record type."""
    record_type = data.get("type", "")

    if record_type == "user":
        return UserRecord.model_validate(data)
    elif record_type == "assistant":
        return AssistantRecord.model_validate(data)
    elif record_type == "system":
        return SystemRecord.model_validate(data)
    elif record_type == "file-history-snapshot":
        return FileHistorySnapshot.model_validate(data)
    else:
        # Fallback to base record for unknown types
        return BaseRecord.model_validate(data)  # type: ignore[return-value]


# Output models for CLI commands
class FileInfo(BaseModel):
    """Output model for info command."""

    file: str
    session_id: str | None
    size_bytes: int
    line_count: int
    record_types: dict[str, int]
    tool_uses: dict[str, int]
    content_types: dict[str, int]
    time_range: dict[str, str | None]
    git_branch: str | None
    cwd: str | None


class ToolCall(BaseModel):
    """Paired tool_use and tool_result."""

    tool_use_id: str
    name: str
    input: dict[str, Any]
    result: dict[str, Any]
    timestamp: datetime | None
    message_uuid: str | None

    # Task-specific fields
    description: str | None = None
    subagent_type: str | None = None
