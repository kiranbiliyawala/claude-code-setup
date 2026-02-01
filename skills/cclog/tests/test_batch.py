"""Tests for the batch module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from cclog.batch import (
    BatchResult,
    FileResult,
    discover_files,
    process_batch,
    process_file_info,
)


class TestFileResult:
    """Tests for FileResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful result."""
        result = FileResult(
            file="/path/to/file.jsonl",
            status="success",
            data={"key": "value"},
        )
        assert result.status == "success"
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_error_result(self) -> None:
        """Test error result."""
        result = FileResult(
            file="/path/to/file.jsonl",
            status="error",
            error={"error": "FILE_NOT_FOUND", "message": "File not found"},
        )
        assert result.status == "error"
        assert result.data is None
        assert result.error is not None

    def test_to_dict(self) -> None:
        """Test result to dict conversion."""
        result = FileResult(
            file="/path/to/file.jsonl",
            status="success",
            data={"info": "data"},
        )
        d = result.to_dict()
        assert d["file"] == "/path/to/file.jsonl"
        assert d["status"] == "success"
        assert d["data"] == {"info": "data"}


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_add_result_success(self) -> None:
        """Test adding successful result."""
        batch = BatchResult()
        batch.add_result(FileResult(file="file1.jsonl", status="success", data={}))
        assert batch.summary["total"] == 1
        assert batch.summary["succeeded"] == 1
        assert batch.summary["failed"] == 0

    def test_add_result_error(self) -> None:
        """Test adding error result."""
        batch = BatchResult()
        batch.add_result(FileResult(file="file1.jsonl", status="error", error={}))
        assert batch.summary["total"] == 1
        assert batch.summary["succeeded"] == 0
        assert batch.summary["failed"] == 1

    def test_add_multiple_results(self) -> None:
        """Test adding multiple results."""
        batch = BatchResult()
        batch.add_result(FileResult(file="file1.jsonl", status="success", data={}))
        batch.add_result(FileResult(file="file2.jsonl", status="error", error={}))
        batch.add_result(FileResult(file="file3.jsonl", status="success", data={}))

        assert batch.summary["total"] == 3
        assert batch.summary["succeeded"] == 2
        assert batch.summary["failed"] == 1

    def test_to_dict(self) -> None:
        """Test batch result to dict conversion."""
        batch = BatchResult()
        batch.add_result(FileResult(file="file1.jsonl", status="success", data={}))
        d = batch.to_dict()

        assert "results" in d
        assert "summary" in d
        assert len(d["results"]) == 1


class TestDiscoverFiles:
    """Tests for discover_files function."""

    def test_discover_explicit_files(self) -> None:
        """Test discovering files from explicit list."""
        files = discover_files(files=["file1.jsonl", "file2.jsonl"])
        assert len(files) == 2
        assert files[0] == Path("file1.jsonl")
        assert files[1] == Path("file2.jsonl")

    def test_discover_no_files(self) -> None:
        """Test with no files specified."""
        files = discover_files()
        assert files == []


class TestProcessFileInfo:
    """Tests for process_file_info function."""

    def test_process_valid_file(self, temp_jsonl_file: Path) -> None:
        """Test processing a valid file."""
        result = process_file_info(temp_jsonl_file)
        assert result.status == "success"
        assert result.data is not None
        assert "line_count" in result.data

    def test_process_nonexistent_file(self) -> None:
        """Test processing a non-existent file."""
        result = process_file_info(Path("/nonexistent/file.jsonl"))
        assert result.status == "error"
        assert result.error is not None
        assert result.error["error"] == "FILE_NOT_FOUND"


class TestProcessBatch:
    """Tests for process_batch function."""

    def test_batch_info(self, temp_jsonl_file: Path) -> None:
        """Test batch info command."""
        result = process_batch(
            files=[temp_jsonl_file],
            command="info",
        )
        assert result.summary["total"] == 1
        assert result.summary["succeeded"] == 1

    def test_batch_nonexistent_files(self) -> None:
        """Test batch with non-existent files."""
        result = process_batch(
            files=[Path("/nonexistent/file1.jsonl"), Path("/nonexistent/file2.jsonl")],
            command="info",
        )
        assert result.summary["total"] == 2
        assert result.summary["failed"] == 2

    def test_batch_fail_fast(self) -> None:
        """Test fail-fast behavior."""
        result = process_batch(
            files=[
                Path("/nonexistent/file1.jsonl"),
                Path("/nonexistent/file2.jsonl"),
                Path("/nonexistent/file3.jsonl"),
            ],
            command="info",
            fail_fast=True,
        )
        # Should stop after first failure
        assert result.summary["failed"] >= 1
        assert result.summary["total"] < 3

    def test_batch_search(self, temp_jsonl_file: Path) -> None:
        """Test batch search command."""
        result = process_batch(
            files=[temp_jsonl_file],
            command="search",
            args={"pattern": "Hello"},
        )
        assert result.summary["total"] == 1
        assert result.summary["succeeded"] == 1

    def test_batch_timeline(self, temp_jsonl_file: Path) -> None:
        """Test batch timeline command."""
        result = process_batch(
            files=[temp_jsonl_file],
            command="timeline",
            args={"summary": True},
        )
        assert result.summary["total"] == 1
        assert result.summary["succeeded"] == 1
        # Check that summary data is present
        assert result.results[0].data is not None
        assert "total_events" in result.results[0].data

    def test_batch_tools(self, temp_jsonl_file: Path) -> None:
        """Test batch tools command."""
        result = process_batch(
            files=[temp_jsonl_file],
            command="tools",
        )
        assert result.summary["total"] == 1
        assert result.summary["succeeded"] == 1

    def test_batch_multiple_files(self, sample_conversation: list[dict[str, Any]]) -> None:
        """Test batch with multiple files."""
        # Create multiple temp files
        files: list[Path] = []
        for _ in range(3):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
                for record in sample_conversation:
                    f.write(json.dumps(record) + "\n")
                files.append(Path(f.name))

        result = process_batch(files=files, command="info")
        assert result.summary["total"] == 3
        assert result.summary["succeeded"] == 3
