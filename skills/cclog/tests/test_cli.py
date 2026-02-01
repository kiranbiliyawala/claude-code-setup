"""Tests for the CLI module."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from cclog.cli import main


class TestInfoCommand:
    """Tests for info command."""

    def test_info_basic(self, temp_jsonl_file: Path) -> None:
        """Test basic info command."""
        runner = CliRunner()
        result = runner.invoke(main, ["info", str(temp_jsonl_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "line_count" in data
        assert "session_id" in data

    def test_info_human_format(self, temp_jsonl_file: Path) -> None:
        """Test info with human format."""
        runner = CliRunner()
        result = runner.invoke(main, ["--format=human", "info", str(temp_jsonl_file)])

        assert result.exit_code == 0
        # Human format outputs a table, not JSON

    def test_info_file_not_found(self) -> None:
        """Test info with non-existent file."""
        runner = CliRunner()
        result = runner.invoke(main, ["info", "/nonexistent/file.jsonl"])

        assert result.exit_code != 0
        data = json.loads(result.output)
        assert data["error"] == "FILE_NOT_FOUND"


class TestMessagesCommand:
    """Tests for messages command."""

    def test_messages_basic(self, temp_jsonl_file: Path) -> None:
        """Test basic messages command."""
        runner = CliRunner()
        result = runner.invoke(main, ["messages", str(temp_jsonl_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_messages_filter_role(self, temp_jsonl_file: Path) -> None:
        """Test messages with role filter."""
        runner = CliRunner()
        result = runner.invoke(main, ["messages", str(temp_jsonl_file), "--role=user"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        for msg in data:
            assert msg["message"]["role"] == "user"

    def test_messages_limit(self, temp_jsonl_file: Path) -> None:
        """Test messages with limit."""
        runner = CliRunner()
        result = runner.invoke(main, ["messages", str(temp_jsonl_file), "--limit=1"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) <= 1


class TestToolsCommand:
    """Tests for tools command."""

    def test_tools_basic(self, temp_jsonl_file: Path) -> None:
        """Test basic tools command."""
        runner = CliRunner()
        result = runner.invoke(main, ["tools", str(temp_jsonl_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_tools_filter_name(self, temp_jsonl_file: Path) -> None:
        """Test tools with name filter."""
        runner = CliRunner()
        result = runner.invoke(main, ["tools", str(temp_jsonl_file), "--name=Read"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        for tool in data:
            assert tool["name"] == "Read"


class TestSearchCommand:
    """Tests for search command."""

    def test_search_basic(self, temp_jsonl_file: Path) -> None:
        """Test basic search command."""
        runner = CliRunner()
        result = runner.invoke(main, ["search", str(temp_jsonl_file), "Hello"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_search_case_insensitive(self, temp_jsonl_file: Path) -> None:
        """Test case insensitive search."""
        runner = CliRunner()
        result = runner.invoke(main, ["search", str(temp_jsonl_file), "hello", "-i"])

        assert result.exit_code == 0


class TestTimelineCommand:
    """Tests for timeline command."""

    def test_timeline_basic(self, temp_jsonl_file: Path) -> None:
        """Test basic timeline command."""
        runner = CliRunner()
        result = runner.invoke(main, ["timeline", str(temp_jsonl_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_timeline_summary(self, temp_jsonl_file: Path) -> None:
        """Test timeline with summary."""
        runner = CliRunner()
        result = runner.invoke(main, ["timeline", str(temp_jsonl_file), "--summary"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_events" in data

    def test_timeline_invalid_timestamp(self, temp_jsonl_file: Path) -> None:
        """Test timeline with invalid timestamp."""
        runner = CliRunner()
        result = runner.invoke(main, ["timeline", str(temp_jsonl_file), "--after=invalid-date"])

        assert result.exit_code != 0
        data = json.loads(result.output)
        assert data["error"] == "TIMESTAMP_PARSE_ERROR"


class TestExportCommand:
    """Tests for export command."""

    def test_export_markdown(self, temp_jsonl_file: Path) -> None:
        """Test markdown export."""
        runner = CliRunner()
        result = runner.invoke(main, ["export", str(temp_jsonl_file), "--format=markdown"])

        assert result.exit_code == 0
        assert "# Conversation Export" in result.output

    def test_export_csv(self, temp_jsonl_file: Path) -> None:
        """Test CSV export."""
        runner = CliRunner()
        result = runner.invoke(main, ["export", str(temp_jsonl_file), "--format=csv"])

        assert result.exit_code == 0
        assert "timestamp" in result.output  # CSV header

    def test_export_llm(self, temp_jsonl_file: Path) -> None:
        """Test LLM export."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["export", str(temp_jsonl_file), "--format=llm", "--max-tokens=1000"]
        )

        assert result.exit_code == 0


class TestBatchCommand:
    """Tests for batch command."""

    def test_batch_info(self, temp_jsonl_file: Path) -> None:
        """Test batch info command."""
        runner = CliRunner()
        files_json = json.dumps([str(temp_jsonl_file)])
        result = runner.invoke(main, ["batch", "info", f"--files={files_json}"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        assert "summary" in data

    def test_batch_search(self, temp_jsonl_file: Path) -> None:
        """Test batch search command."""
        runner = CliRunner()
        files_json = json.dumps([str(temp_jsonl_file)])
        result = runner.invoke(main, ["batch", "search", "Hello", f"--files={files_json}"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["summary"]["total"] == 1

    def test_batch_no_files(self) -> None:
        """Test batch with no files."""
        runner = CliRunner()
        result = runner.invoke(main, ["batch", "info"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["error"] == "NO_FILES"


class TestCapabilitiesCommand:
    """Tests for capabilities command."""

    def test_capabilities(self) -> None:
        """Test capabilities command."""
        runner = CliRunner()
        result = runner.invoke(main, ["capabilities"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "commands" in data
        assert "batch" in data["commands"]
        assert "parallel_processing" in data["features"]
