"""Tests for the parser module."""

from __future__ import annotations

from pathlib import Path

import pytest

from cclog.errors import FileNotFoundCclogError, InvalidJsonlError
from cclog.models import AssistantRecord, UserRecord
from cclog.parser import get_file_info, parse_jsonl


class TestParseJsonl:
    """Tests for parse_jsonl function."""

    def test_parse_valid_jsonl(self, temp_jsonl_file: Path) -> None:
        """Test parsing a valid JSONL file."""
        records = list(parse_jsonl(temp_jsonl_file))
        assert len(records) == 3
        assert isinstance(records[0], UserRecord)
        assert isinstance(records[1], AssistantRecord)
        assert isinstance(records[2], UserRecord)

    def test_parse_empty_file(self, empty_jsonl_file: Path) -> None:
        """Test parsing an empty JSONL file."""
        records = list(parse_jsonl(empty_jsonl_file))
        assert records == []

    def test_parse_file_not_found(self) -> None:
        """Test parsing a non-existent file."""
        with pytest.raises(FileNotFoundCclogError) as exc_info:
            list(parse_jsonl("/nonexistent/file.jsonl"))
        assert "File not found" in str(exc_info.value)

    def test_parse_malformed_jsonl(self, malformed_jsonl_file: Path) -> None:
        """Test parsing a file with invalid JSON."""
        with pytest.raises(InvalidJsonlError) as exc_info:
            list(parse_jsonl(malformed_jsonl_file))
        assert exc_info.value.code == "E1002"
        assert "line_number" in exc_info.value.details


class TestGetFileInfo:
    """Tests for get_file_info function."""

    def test_file_info_basic(self, temp_jsonl_file: Path) -> None:
        """Test basic file info extraction."""
        info = get_file_info(temp_jsonl_file)
        assert info.line_count == 3
        assert info.session_id == "session-001"
        assert "user" in info.record_types
        assert "assistant" in info.record_types

    def test_file_info_tool_uses(self, temp_jsonl_file: Path) -> None:
        """Test tool usage extraction in file info."""
        info = get_file_info(temp_jsonl_file)
        assert "Read" in info.tool_uses
        assert info.tool_uses["Read"] == 1

    def test_file_info_time_range(self, temp_jsonl_file: Path) -> None:
        """Test time range extraction."""
        info = get_file_info(temp_jsonl_file)
        assert info.time_range["first"] is not None
        assert info.time_range["last"] is not None

    def test_file_info_not_found(self) -> None:
        """Test file info for non-existent file."""
        with pytest.raises(FileNotFoundCclogError):
            get_file_info("/nonexistent/file.jsonl")
