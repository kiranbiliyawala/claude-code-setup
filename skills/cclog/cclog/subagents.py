"""Subagent discovery and session linking."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from cclog.models import (
    AssistantRecord,
    ConversationRecord,
    ToolResultBlock,
    ToolUseBlock,
    UserRecord,
)
from cclog.parser import parse_jsonl


@dataclass
class SubagentInfo:
    """Information about a subagent invocation.

    Contains the Task tool call details and linked subagent file.
    """

    agent_id: str
    description: str | None
    subagent_type: str | None
    tool_use_id: str
    timestamp: datetime | None
    message_uuid: str | None

    # Linked file info
    file_path: Path | None = None
    file_exists: bool = False

    # Result metadata
    status: str | None = None
    duration_ms: int | None = None
    total_tokens: int | None = None
    tool_use_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON output."""
        result: dict[str, Any] = {
            "agent_id": self.agent_id,
            "tool_use_id": self.tool_use_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message_uuid": self.message_uuid,
            "file_exists": self.file_exists,
        }

        if self.description:
            result["description"] = self.description
        if self.subagent_type:
            result["subagent_type"] = self.subagent_type
        if self.file_path:
            result["file_path"] = str(self.file_path)
        if self.status:
            result["status"] = self.status
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.total_tokens is not None:
            result["total_tokens"] = self.total_tokens
        if self.tool_use_count is not None:
            result["tool_use_count"] = self.tool_use_count

        return result


@dataclass
class SubagentTree:
    """Hierarchical view of session and its subagents.

    Represents the parent session with all spawned subagents.
    """

    session_id: str
    file_path: Path
    subagents: list[SubagentInfo] = field(default_factory=lambda: [])

    # Nested subagents (subagents that spawn their own subagents)
    children: dict[str, SubagentTree] = field(default_factory=lambda: {})

    def to_dict(self, include_children: bool = True) -> dict[str, Any]:
        """Convert to dict for JSON output."""
        result: dict[str, Any] = {
            "session_id": self.session_id,
            "file_path": str(self.file_path),
            "subagents": [s.to_dict() for s in self.subagents],
        }

        if include_children and self.children:
            result["children"] = {
                agent_id: tree.to_dict(include_children=True)
                for agent_id, tree in self.children.items()
            }

        return result


def path_to_project_dir(project_path: str | Path) -> str:
    """Convert a project path to Claude's directory name format.

    Claude stores projects in ~/.claude/projects/ with paths converted:
    /Users/foo/project -> -Users-foo-project

    Args:
        project_path: Absolute path to the project

    Returns:
        Directory name in Claude's format
    """
    path = Path(project_path).resolve()
    # Replace / with - and prepend -
    return "-" + str(path).replace("/", "-").lstrip("-")


def find_project_dir(project_path: str | Path) -> Path | None:
    """Find the Claude project directory for a given project path.

    Args:
        project_path: Path to the project

    Returns:
        Path to the Claude project directory, or None if not found
    """
    claude_dir = Path.home() / ".claude" / "projects"
    if not claude_dir.exists():
        return None

    dir_name = path_to_project_dir(project_path)
    project_dir = claude_dir / dir_name

    if project_dir.exists():
        return project_dir
    return None


def find_project_dir_from_file(file_path: str | Path) -> Path | None:
    """Get the project directory from a session file path.

    Args:
        file_path: Path to a session JSONL file

    Returns:
        Path to the project directory
    """
    path = Path(file_path).resolve()
    return path.parent if path.parent.exists() else None


def get_session_id_from_file(file_path: str | Path) -> str | None:
    """Extract session ID from a file by reading first record.

    Args:
        file_path: Path to session JSONL file

    Returns:
        Session ID or None if not found
    """
    path = Path(file_path)
    if not path.exists():
        return None

    try:
        with open(path) as f:
            first_line = f.readline()
            if first_line:
                import orjson

                data = orjson.loads(first_line)
                return data.get("sessionId")
    except (OSError, ValueError):
        return None
    return None


def find_subagent_file(project_dir: Path, agent_id: str) -> Path | None:
    """Find the subagent file for a given agent ID.

    Subagent files are named: agent-{agent_id}.jsonl

    Args:
        project_dir: Path to the Claude project directory
        agent_id: The agent ID (e.g., "a3f5885")

    Returns:
        Path to the subagent file, or None if not found
    """
    agent_file = project_dir / f"agent-{agent_id}.jsonl"
    if agent_file.exists():
        return agent_file
    return None


def find_session_files(project_dir: Path, session_id: str) -> list[Path]:
    """Find all session files related to a session ID.

    This includes the main session file and all subagent files
    that reference this session.

    Args:
        project_dir: Path to the Claude project directory
        session_id: The session ID to search for

    Returns:
        List of related file paths
    """
    related_files: list[Path] = []

    # Check main session file
    main_file = project_dir / f"{session_id}.jsonl"
    if main_file.exists():
        related_files.append(main_file)

    # Scan agent files for matching sessionId
    for agent_file in project_dir.glob("agent-*.jsonl"):
        file_session_id = get_session_id_from_file(agent_file)
        if file_session_id == session_id:
            related_files.append(agent_file)

    return related_files


def extract_subagents(
    records: Iterator[ConversationRecord],
    project_dir: Path | None = None,
) -> Iterator[SubagentInfo]:
    """Extract subagent information from Task tool calls.

    Parses tool_result blocks to find agentId from toolUseResult,
    then links to the corresponding subagent file.

    Args:
        records: Iterator of conversation records
        project_dir: Path to project directory for file linking

    Yields:
        SubagentInfo for each Task tool call with an agentId
    """
    # Store pending Task tool_use blocks
    pending_tasks: dict[str, tuple[str | None, str | None, datetime | None, str | None]] = {}

    for record in records:
        # Track Task tool_use blocks from assistant messages
        if isinstance(record, AssistantRecord):
            for block in record.message.get_content_blocks():
                if isinstance(block, ToolUseBlock) and block.name == "Task":
                    # Store description, subagent_type, timestamp, message_uuid
                    pending_tasks[block.id] = (
                        block.description,
                        block.subagent_type,
                        record.timestamp,
                        record.uuid,
                    )

        # Look for tool_result with toolUseResult containing agentId
        elif isinstance(record, UserRecord):
            for block in record.message.get_content_blocks():
                if isinstance(block, ToolResultBlock) and block.tool_use_id in pending_tasks:
                    # Extract agentId from the content text
                    agent_id = _extract_agent_id_from_result(block)

                    if agent_id:
                        desc, subagent_type, timestamp, message_uuid = pending_tasks.pop(
                            block.tool_use_id
                        )

                        # Find the linked file
                        file_path = None
                        file_exists = False
                        if project_dir:
                            file_path = find_subagent_file(project_dir, agent_id)
                            file_exists = file_path is not None
                            if not file_exists:
                                # Still provide expected path
                                file_path = project_dir / f"agent-{agent_id}.jsonl"

                        yield SubagentInfo(
                            agent_id=agent_id,
                            description=desc,
                            subagent_type=subagent_type,
                            tool_use_id=block.tool_use_id,
                            timestamp=timestamp,
                            message_uuid=message_uuid,
                            file_path=file_path,
                            file_exists=file_exists,
                        )


def _extract_agent_id_from_result(block: ToolResultBlock) -> str | None:
    """Extract agentId from tool result content.

    The agentId appears in the content as:
    "agentId: a3f5885 (for resuming...)"
    """
    content = block.content_text
    # Look for pattern: agentId: {id}
    import re

    match = re.search(r"agentId:\s*([a-f0-9]+)", content)
    if match:
        return match.group(1)
    return None


def build_subagent_tree(
    file_path: str | Path,
    max_depth: int = 10,
) -> SubagentTree:
    """Build a hierarchical tree of subagents from a session file.

    Recursively follows subagent files to build full tree.

    Args:
        file_path: Path to the root session file
        max_depth: Maximum recursion depth to prevent infinite loops

    Returns:
        SubagentTree with all subagents and their children
    """
    path = Path(file_path).resolve()
    project_dir = path.parent

    session_id = get_session_id_from_file(path)
    if not session_id:
        # Try to extract from filename (remove "agent-" prefix if present)
        session_id = path.stem[6:] if path.stem.startswith("agent-") else path.stem

    tree = SubagentTree(
        session_id=session_id,
        file_path=path,
    )

    if max_depth <= 0:
        return tree

    # Extract subagents from this file
    records = parse_jsonl(path)
    for subagent in extract_subagents(records, project_dir):
        tree.subagents.append(subagent)

        # Recursively build tree for subagent files
        if subagent.file_exists and subagent.file_path:
            child_tree = build_subagent_tree(subagent.file_path, max_depth - 1)
            tree.children[subagent.agent_id] = child_tree

    return tree


def find_parent_session(
    file_path: str | Path,
) -> Path | None:
    """Find the parent session file for a subagent file.

    Reads the sessionId from the subagent file and finds the main session.

    Args:
        file_path: Path to a subagent file

    Returns:
        Path to the parent session file, or None if not found
    """
    path = Path(file_path).resolve()

    # Must be an agent file
    if not path.stem.startswith("agent-"):
        return None

    session_id = get_session_id_from_file(path)
    if not session_id:
        return None

    # Look for main session file
    project_dir = path.parent
    main_file = project_dir / f"{session_id}.jsonl"

    if main_file.exists():
        return main_file

    return None
