"""Streaming JSONL parser for Claude Code conversation files."""

from __future__ import annotations

import os
from collections import Counter
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import orjson
from pydantic import ValidationError

from cclog.errors import FileNotFoundCclogError, InvalidJsonlError, NotClaudeLogError
from cclog.models import (
    AssistantRecord,
    ConversationRecord,
    FileInfo,
    ToolUseBlock,
    UserRecord,
    parse_record,
)


def parse_jsonl(path: str | Path) -> Iterator[ConversationRecord]:
    """
    Parse a JSONL file yielding conversation records.

    Streams records one at a time to handle large files efficiently.
    Never loads the full file into memory.

    Args:
        path: Path to the JSONL file

    Yields:
        ConversationRecord instances

    Raises:
        FileNotFoundError_: If file doesn't exist
        InvalidJsonlError: If a line isn't valid JSON
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundCclogError(str(path))

    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data = orjson.loads(line)
            except orjson.JSONDecodeError as e:
                raise InvalidJsonlError(str(path), line_num, str(e)) from e

            try:
                yield parse_record(data)
            except ValidationError:
                # Skip records that don't match our models
                # This allows forward compatibility with new record types
                continue


def parse_jsonl_raw(path: str | Path) -> Iterator[dict[str, Any]]:
    """
    Parse a JSONL file yielding raw dicts.

    Use this when you need access to fields not in our models.

    Args:
        path: Path to the JSONL file

    Yields:
        Raw dict for each line

    Raises:
        FileNotFoundError_: If file doesn't exist
        InvalidJsonlError: If a line isn't valid JSON
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundCclogError(str(path))

    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                yield orjson.loads(line)
            except orjson.JSONDecodeError as e:
                raise InvalidJsonlError(str(path), line_num, str(e)) from e


def validate_claude_log(path: str | Path) -> None:
    """
    Validate that a file appears to be a Claude Code conversation log.

    Args:
        path: Path to the JSONL file

    Raises:
        NotClaudeLogError: If file doesn't look like a Claude log
    """
    path = Path(path)
    has_user = False
    has_assistant = False
    has_session_id = False

    for record in parse_jsonl_raw(path):
        record_type = record.get("type", "")
        if record_type == "user":
            has_user = True
        elif record_type == "assistant":
            has_assistant = True
        if "sessionId" in record:
            has_session_id = True

        # Early exit once we've seen enough
        if has_user and has_assistant and has_session_id:
            return

    missing: list[str] = []
    if not has_user:
        missing.append("user messages")
    if not has_assistant:
        missing.append("assistant messages")
    if not has_session_id:
        missing.append("sessionId")

    if missing:
        raise NotClaudeLogError(str(path), missing)


def get_file_info(path: str | Path) -> FileInfo:
    """
    Get metadata about a conversation file without loading full content.

    Args:
        path: Path to the JSONL file

    Returns:
        FileInfo with file metadata
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundCclogError(str(path))

    size_bytes = path.stat().st_size
    line_count = 0
    record_types: Counter[str] = Counter()
    tool_uses: Counter[str] = Counter()
    content_types: Counter[str] = Counter()
    timestamps: list[datetime] = []
    session_id: str | None = None
    git_branch: str | None = None
    cwd: str | None = None

    for record in parse_jsonl(path):
        line_count += 1
        record_types[record.type] += 1

        # Extract metadata from first record that has it
        if session_id is None and record.session_id:
            session_id = record.session_id
        if git_branch is None and record.git_branch:
            git_branch = record.git_branch
        if cwd is None and record.cwd:
            cwd = record.cwd

        # Collect timestamps
        if record.timestamp:
            timestamps.append(record.timestamp)

        # Count content types and tool uses from messages
        if isinstance(record, (UserRecord, AssistantRecord)):
            for block in record.message.get_content_blocks():
                content_types[block.type] += 1
                if isinstance(block, ToolUseBlock):
                    tool_uses[block.name] += 1

    # Calculate time range
    time_range: dict[str, str | None] = {"first": None, "last": None}
    if timestamps:
        timestamps.sort()
        time_range["first"] = timestamps[0].isoformat()
        time_range["last"] = timestamps[-1].isoformat()

    return FileInfo(
        file=str(path),
        session_id=session_id,
        size_bytes=size_bytes,
        line_count=line_count,
        record_types=dict(record_types),
        tool_uses=dict(tool_uses),
        content_types=dict(content_types),
        time_range=time_range,
        git_branch=git_branch,
        cwd=cwd,
    )


def find_project_dir(project_path: str) -> Path:
    """
    Convert a project path to Claude's hash format directory.

    Claude stores conversation logs in:
    ~/.claude/projects/-Users-username-path-to-project/

    Args:
        project_path: Absolute path to the project

    Returns:
        Path to the Claude project directory
    """
    # Normalize path and replace separators with dashes
    normalized = os.path.abspath(project_path)
    # Remove leading slash and replace remaining with dashes
    hashed = normalized.replace("/", "-")
    if hashed.startswith("-"):
        hashed = hashed[1:]

    claude_dir = Path.home() / ".claude" / "projects" / hashed
    return claude_dir


def list_conversation_files(project_path: str | None = None) -> Iterator[Path]:
    """
    List all JSONL conversation files for a project.

    Args:
        project_path: Optional project path. If None, lists all projects.

    Yields:
        Paths to JSONL files
    """
    if project_path:
        project_dir = find_project_dir(project_path)
        if project_dir.exists():
            yield from project_dir.glob("*.jsonl")
    else:
        # List all projects
        claude_projects = Path.home() / ".claude" / "projects"
        if claude_projects.exists():
            for project_dir in claude_projects.iterdir():
                if project_dir.is_dir():
                    yield from project_dir.glob("*.jsonl")
