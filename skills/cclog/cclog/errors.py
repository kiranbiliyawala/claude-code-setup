"""Error taxonomy for cclog CLI."""

from __future__ import annotations

import sys
from typing import Any

import orjson


class CclogError(Exception):
    """Base error for cclog CLI."""

    error_type: str = "INTERNAL_ERROR"
    code: str = "E9001"

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        suggestion: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.field = field
        self.suggestion = suggestion
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to JSON-serializable dict."""
        result: dict[str, Any] = {
            "error": self.error_type,
            "code": self.code,
            "message": self.message,
        }
        if self.field:
            result["field"] = self.field
        if self.suggestion:
            result["suggestion"] = self.suggestion
        if self.details:
            result["details"] = self.details
        return result

    def to_json(self) -> bytes:
        """Convert error to JSON bytes."""
        return orjson.dumps(self.to_dict(), option=orjson.OPT_INDENT_2)


class FileNotFoundCclogError(CclogError):
    """File not found error (E1001)."""

    error_type = "FILE_NOT_FOUND"
    code = "E1001"

    def __init__(self, path: str) -> None:
        super().__init__(
            f"File not found: {path}",
            field="file",
            suggestion="Check that the file path exists and is accessible",
            details={"path": path},
        )


class InvalidJsonlError(CclogError):
    """Invalid JSONL format error (E1002)."""

    error_type = "INVALID_JSONL"
    code = "E1002"

    def __init__(self, path: str, line_number: int, parse_error: str) -> None:
        super().__init__(
            f"Line {line_number} is not valid JSON: {parse_error}",
            field="content",
            suggestion="The file may be corrupted or not a valid JSONL file",
            details={"path": path, "line_number": line_number, "parse_error": parse_error},
        )


class NotClaudeLogError(CclogError):
    """Not a Claude Code log file error (E1003)."""

    error_type = "NOT_CLAUDE_LOG"
    code = "E1003"

    def __init__(self, path: str, missing_fields: list[str]) -> None:
        super().__init__(
            "File does not appear to be a Claude Code conversation log",
            field="content",
            suggestion="Ensure the file is from ~/.claude/projects/*/",
            details={"path": path, "missing_fields": missing_fields},
        )


class FilterInvalidError(CclogError):
    """Invalid filter error (E2001)."""

    error_type = "FILTER_INVALID"
    code = "E2001"

    def __init__(self, filter_name: str, valid_values: list[str] | None = None) -> None:
        suggestion = "Use --help for valid filter options"
        if valid_values:
            suggestion = f"Valid values: {', '.join(valid_values)}"
        super().__init__(
            f"Unknown or invalid filter: {filter_name}",
            field="filter",
            suggestion=suggestion,
            details={"filter": filter_name, "valid_values": valid_values},
        )


class RegexInvalidError(CclogError):
    """Invalid regex pattern error (E2002)."""

    error_type = "REGEX_INVALID"
    code = "E2002"

    def __init__(self, pattern: str, error: str) -> None:
        super().__init__(
            f"Invalid regex pattern: {error}",
            field="pattern",
            suggestion="Check regex syntax; use --no-regex for literal search",
            details={"pattern": pattern, "error": error},
        )


class SessionNotFoundError(CclogError):
    """Session not found error (E3001)."""

    error_type = "SESSION_NOT_FOUND"
    code = "E3001"

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"No files found for session: {session_id}",
            field="session_id",
            suggestion="The session may not exist or files may have been deleted",
            details={"session_id": session_id},
        )


class EmptyFileError(CclogError):
    """Empty file error (E1004)."""

    error_type = "EMPTY_FILE"
    code = "E1004"

    def __init__(self, path: str) -> None:
        super().__init__(
            f"File is empty: {path}",
            field="file",
            suggestion="The file has no content; it may be a new or corrupted session",
            details={"path": path},
        )


class ProjectNotFoundError(CclogError):
    """Project directory not found error (E1005)."""

    error_type = "PROJECT_NOT_FOUND"
    code = "E1005"

    def __init__(self, project_path: str, expected_dir: str) -> None:
        super().__init__(
            f"No Claude project directory found for: {project_path}",
            field="project",
            suggestion="Ensure you have used Claude Code in this project directory",
            details={"project_path": project_path, "expected_dir": expected_dir},
        )


class NoFilesError(CclogError):
    """No files to process error (E4001)."""

    error_type = "NO_FILES"
    code = "E4001"

    def __init__(self, project: str | None = None) -> None:
        message = "No files to process"
        if project:
            message = f"No JSONL files found in project: {project}"
        super().__init__(
            message,
            field="files",
            suggestion="Use --files to specify files or --project for a valid project path",
            details={"project": project} if project else {},
        )


class InvalidCommandError(CclogError):
    """Invalid batch command error (E4002)."""

    error_type = "INVALID_COMMAND"
    code = "E4002"

    def __init__(self, command: str, valid_commands: list[str]) -> None:
        super().__init__(
            f"Unknown batch command: {command}",
            field="command",
            suggestion=f"Valid commands: {', '.join(valid_commands)}",
            details={"command": command, "valid_commands": valid_commands},
        )


class TimestampParseError(CclogError):
    """Timestamp parsing error (E2003)."""

    error_type = "TIMESTAMP_PARSE_ERROR"
    code = "E2003"

    def __init__(self, value: str, expected_format: str = "ISO 8601") -> None:
        super().__init__(
            f"Cannot parse timestamp: {value}",
            field="timestamp",
            suggestion=f"Use {expected_format} format (e.g., 2025-01-01T00:00:00Z)",
            details={"value": value, "expected_format": expected_format},
        )


# Exit codes following agent-cli-design conventions
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_INVALID_ARGS = 2
EXIT_AUTH_ERROR = 3
EXIT_AUTHZ_ERROR = 4
EXIT_NOT_FOUND = 5
EXIT_CONFLICT = 6
EXIT_RATE_LIMITED = 7
EXIT_PARTIAL_SUCCESS = 8


def get_exit_code(error: CclogError) -> int:
    """Get appropriate exit code for an error."""
    code_map = {
        "FILE_NOT_FOUND": EXIT_NOT_FOUND,
        "SESSION_NOT_FOUND": EXIT_NOT_FOUND,
        "PROJECT_NOT_FOUND": EXIT_NOT_FOUND,
        "NO_FILES": EXIT_NOT_FOUND,
        "EMPTY_FILE": EXIT_INVALID_ARGS,
        "INVALID_JSONL": EXIT_INVALID_ARGS,
        "NOT_CLAUDE_LOG": EXIT_INVALID_ARGS,
        "FILTER_INVALID": EXIT_INVALID_ARGS,
        "REGEX_INVALID": EXIT_INVALID_ARGS,
        "INVALID_COMMAND": EXIT_INVALID_ARGS,
        "TIMESTAMP_PARSE_ERROR": EXIT_INVALID_ARGS,
    }
    return code_map.get(error.error_type, EXIT_GENERAL_ERROR)


def handle_error(error: CclogError) -> None:
    """Print error as JSON and exit with appropriate code."""
    sys.stdout.buffer.write(error.to_json())
    sys.stdout.buffer.write(b"\n")
    sys.exit(get_exit_code(error))
