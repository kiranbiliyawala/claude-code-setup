"""Tests for the errors module."""

from __future__ import annotations

import json

from cclog.errors import (
    EXIT_INVALID_ARGS,
    EXIT_NOT_FOUND,
    CclogError,
    EmptyFileError,
    FileNotFoundCclogError,
    FilterInvalidError,
    InvalidCommandError,
    InvalidJsonlError,
    NoFilesError,
    NotClaudeLogError,
    ProjectNotFoundError,
    RegexInvalidError,
    SessionNotFoundError,
    TimestampParseError,
    get_exit_code,
)


class TestCclogError:
    """Tests for base CclogError class."""

    def test_to_dict(self) -> None:
        """Test error to dict conversion."""
        error = CclogError(
            "Test error",
            field="test_field",
            suggestion="Try this",
            details={"key": "value"},
        )
        result = error.to_dict()

        assert result["error"] == "INTERNAL_ERROR"
        assert result["code"] == "E9001"
        assert result["message"] == "Test error"
        assert result["field"] == "test_field"
        assert result["suggestion"] == "Try this"
        assert result["details"] == {"key": "value"}

    def test_to_json(self) -> None:
        """Test error to JSON conversion."""
        error = CclogError("Test error")
        json_bytes = error.to_json()
        parsed = json.loads(json_bytes)

        assert parsed["message"] == "Test error"

    def test_optional_fields(self) -> None:
        """Test that optional fields are excluded when not set."""
        error = CclogError("Test error")
        result = error.to_dict()

        assert "field" not in result
        assert "suggestion" not in result
        assert "details" not in result


class TestSpecificErrors:
    """Tests for specific error types."""

    def test_file_not_found_error(self) -> None:
        """Test FileNotFoundCclogError."""
        error = FileNotFoundCclogError("/path/to/file.jsonl")
        assert error.code == "E1001"
        assert error.error_type == "FILE_NOT_FOUND"
        assert "/path/to/file.jsonl" in error.message
        assert error.details["path"] == "/path/to/file.jsonl"

    def test_invalid_jsonl_error(self) -> None:
        """Test InvalidJsonlError."""
        error = InvalidJsonlError("/path/to/file.jsonl", 42, "Unexpected character")
        assert error.code == "E1002"
        assert "Line 42" in error.message
        assert error.details["line_number"] == 42

    def test_not_claude_log_error(self) -> None:
        """Test NotClaudeLogError."""
        error = NotClaudeLogError("/path/to/file.jsonl", ["user messages", "sessionId"])
        assert error.code == "E1003"
        assert "user messages" in str(error.details["missing_fields"])

    def test_filter_invalid_error(self) -> None:
        """Test FilterInvalidError."""
        error = FilterInvalidError("--invalid", ["valid1", "valid2"])
        assert error.code == "E2001"
        assert "valid1" in str(error.suggestion)

    def test_regex_invalid_error(self) -> None:
        """Test RegexInvalidError."""
        error = RegexInvalidError("[invalid", "Missing closing bracket")
        assert error.code == "E2002"
        assert "[invalid" in str(error.details)

    def test_session_not_found_error(self) -> None:
        """Test SessionNotFoundError."""
        error = SessionNotFoundError("abc-123")
        assert error.code == "E3001"
        assert "abc-123" in error.message

    def test_empty_file_error(self) -> None:
        """Test EmptyFileError."""
        error = EmptyFileError("/path/to/file.jsonl")
        assert error.code == "E1004"
        assert "empty" in error.message.lower()

    def test_project_not_found_error(self) -> None:
        """Test ProjectNotFoundError."""
        error = ProjectNotFoundError("/path/to/project", "/expected/dir")
        assert error.code == "E1005"
        assert error.details["project_path"] == "/path/to/project"

    def test_no_files_error(self) -> None:
        """Test NoFilesError."""
        error = NoFilesError("/path/to/project")
        assert error.code == "E4001"
        assert error.suggestion is not None
        assert "project" in error.suggestion.lower()

    def test_invalid_command_error(self) -> None:
        """Test InvalidCommandError."""
        error = InvalidCommandError("invalid", ["info", "search"])
        assert error.code == "E4002"
        assert error.suggestion is not None
        assert "info" in error.suggestion

    def test_timestamp_parse_error(self) -> None:
        """Test TimestampParseError."""
        error = TimestampParseError("not-a-date")
        assert error.code == "E2003"
        assert error.suggestion is not None
        assert "ISO 8601" in error.suggestion


class TestExitCodes:
    """Tests for exit code mapping."""

    def test_file_not_found_exit_code(self) -> None:
        """Test FILE_NOT_FOUND maps to EXIT_NOT_FOUND."""
        error = FileNotFoundCclogError("/path/to/file.jsonl")
        assert get_exit_code(error) == EXIT_NOT_FOUND

    def test_invalid_jsonl_exit_code(self) -> None:
        """Test INVALID_JSONL maps to EXIT_INVALID_ARGS."""
        error = InvalidJsonlError("/path/to/file.jsonl", 1, "error")
        assert get_exit_code(error) == EXIT_INVALID_ARGS

    def test_timestamp_parse_exit_code(self) -> None:
        """Test TIMESTAMP_PARSE_ERROR maps to EXIT_INVALID_ARGS."""
        error = TimestampParseError("invalid")
        assert get_exit_code(error) == EXIT_INVALID_ARGS

    def test_no_files_exit_code(self) -> None:
        """Test NO_FILES maps to EXIT_NOT_FOUND."""
        error = NoFilesError()
        assert get_exit_code(error) == EXIT_NOT_FOUND
