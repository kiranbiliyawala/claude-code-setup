"""Shared test fixtures for cclog tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_user_record() -> dict[str, Any]:
    """A sample user record."""
    return {
        "type": "user",
        "uuid": "user-001",
        "sessionId": "session-001",
        "timestamp": "2025-01-01T10:00:00Z",
        "message": {
            "role": "user",
            "content": [{"type": "text", "text": "Hello, Claude!"}],
        },
    }


@pytest.fixture
def sample_assistant_record() -> dict[str, Any]:
    """A sample assistant record."""
    return {
        "type": "assistant",
        "uuid": "assistant-001",
        "sessionId": "session-001",
        "timestamp": "2025-01-01T10:00:05Z",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hello! How can I help you?"},
                {
                    "type": "tool_use",
                    "id": "tool-001",
                    "name": "Read",
                    "input": {"file_path": "/path/to/file.txt"},
                },
            ],
        },
    }


@pytest.fixture
def sample_tool_result_record() -> dict[str, Any]:
    """A sample user record with tool result."""
    return {
        "type": "user",
        "uuid": "user-002",
        "sessionId": "session-001",
        "timestamp": "2025-01-01T10:00:10Z",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool-001",
                    "content": "File contents here...",
                    "is_error": False,
                }
            ],
        },
    }


@pytest.fixture
def sample_task_record() -> dict[str, Any]:
    """A sample assistant record with Task tool use."""
    return {
        "type": "assistant",
        "uuid": "assistant-002",
        "sessionId": "session-001",
        "timestamp": "2025-01-01T10:00:15Z",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "task-001",
                    "name": "Task",
                    "input": {
                        "prompt": "Search for files",
                        "description": "Find matching files",
                        "subagent_type": "Explore",
                    },
                }
            ],
        },
    }


@pytest.fixture
def sample_conversation(
    sample_user_record: dict[str, Any],
    sample_assistant_record: dict[str, Any],
    sample_tool_result_record: dict[str, Any],
) -> list[dict[str, Any]]:
    """A complete sample conversation."""
    return [sample_user_record, sample_assistant_record, sample_tool_result_record]


@pytest.fixture
def temp_jsonl_file(sample_conversation: list[dict[str, Any]]) -> Path:
    """Create a temporary JSONL file with sample data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for record in sample_conversation:
            f.write(json.dumps(record) + "\n")
        return Path(f.name)


@pytest.fixture
def empty_jsonl_file() -> Path:
    """Create an empty JSONL file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        return Path(f.name)


@pytest.fixture
def malformed_jsonl_file() -> Path:
    """Create a JSONL file with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"type": "user"}\n')
        f.write("not valid json\n")
        f.write('{"type": "assistant"}\n')
        return Path(f.name)
