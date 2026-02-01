"""Batch processing for multiple conversation files."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from cclog.errors import CclogError, FileNotFoundCclogError
from cclog.parser import get_file_info, list_conversation_files, parse_jsonl


@dataclass
class FileResult:
    """Result of processing a single file."""

    file: str
    status: Literal["success", "error"]
    data: Any = None
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON output."""
        result: dict[str, Any] = {
            "file": self.file,
            "status": self.status,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        return result


def _default_results() -> list[FileResult]:
    return []


def _default_summary() -> dict[str, int]:
    return {}


@dataclass
class BatchResult:
    """Aggregate result of batch processing."""

    results: list[FileResult] = field(default_factory=_default_results)
    summary: dict[str, int] = field(default_factory=_default_summary)

    def __post_init__(self) -> None:
        """Initialize summary."""
        if not self.summary:
            self.summary = {"total": 0, "succeeded": 0, "failed": 0}

    def add_result(self, result: FileResult) -> None:
        """Add a file result and update summary."""
        self.results.append(result)
        self.summary["total"] += 1
        if result.status == "success":
            self.summary["succeeded"] += 1
        else:
            self.summary["failed"] += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON output."""
        return {
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
        }


def discover_files(
    project: str | None = None,
    files: list[str] | None = None,
) -> list[Path]:
    """
    Discover conversation files to process.

    Args:
        project: Project path to auto-discover files from
        files: Explicit list of file paths

    Returns:
        List of file paths to process
    """
    if files:
        return [Path(f) for f in files]

    if project:
        return list(list_conversation_files(project))

    return []


def process_file_info(file_path: Path) -> FileResult:
    """Process a single file with the info command."""
    try:
        info = get_file_info(str(file_path))
        return FileResult(
            file=str(file_path),
            status="success",
            data=info.model_dump(mode="json"),
        )
    except CclogError as e:
        return FileResult(
            file=str(file_path),
            status="error",
            error=e.to_dict(),
        )
    except Exception as e:
        return FileResult(
            file=str(file_path),
            status="error",
            error={"error": "UNEXPECTED_ERROR", "message": str(e)},
        )


def process_file_search(file_path: Path, pattern: str, **kwargs: Any) -> FileResult:
    """Process a single file with the search command."""
    from cclog.search import SearchFilter, search_content

    try:
        filter_ = SearchFilter(
            pattern=pattern,
            scope=kwargs.get("scope", "all"),
            regex=kwargs.get("regex", False),
            case_insensitive=kwargs.get("case_insensitive", False),
            context_lines=kwargs.get("context_lines", 0),
            limit=kwargs.get("limit"),
            offset=kwargs.get("offset", 0),
        )

        records = parse_jsonl(str(file_path))
        matches = list(search_content(records, filter_))

        return FileResult(
            file=str(file_path),
            status="success",
            data={
                "match_count": len(matches),
                "matches": [m.to_dict() for m in matches],
            },
        )
    except CclogError as e:
        return FileResult(
            file=str(file_path),
            status="error",
            error=e.to_dict(),
        )
    except Exception as e:
        return FileResult(
            file=str(file_path),
            status="error",
            error={"error": "UNEXPECTED_ERROR", "message": str(e)},
        )


def process_file_tools(file_path: Path, **kwargs: Any) -> FileResult:
    """Process a single file with the tools command."""
    from cclog.tools import ToolFilter, get_tools

    try:
        filter_ = ToolFilter(
            name=kwargs.get("name"),
            subagent_type=kwargs.get("subagent_type"),
            status=kwargs.get("status"),
            limit=kwargs.get("limit"),
            offset=kwargs.get("offset", 0),
        )

        tools = list(get_tools(str(file_path), filter_=filter_, full=kwargs.get("full", False)))

        return FileResult(
            file=str(file_path),
            status="success",
            data={
                "tool_count": len(tools),
                "tools": tools,
            },
        )
    except CclogError as e:
        return FileResult(
            file=str(file_path),
            status="error",
            error=e.to_dict(),
        )
    except Exception as e:
        return FileResult(
            file=str(file_path),
            status="error",
            error={"error": "UNEXPECTED_ERROR", "message": str(e)},
        )


def process_file_timeline(file_path: Path, **kwargs: Any) -> FileResult:
    """Process a single file with the timeline command."""
    from cclog.timeline import TimelineFilter, build_timeline, get_timeline_summary

    try:
        filter_ = TimelineFilter(
            after=kwargs.get("after"),
            before=kwargs.get("before"),
            event_types=kwargs.get("event_types"),
            tool_names=kwargs.get("tool_names"),
            group_by=kwargs.get("group_by"),
            limit=kwargs.get("limit"),
            offset=kwargs.get("offset", 0),
        )

        records = parse_jsonl(str(file_path))
        events = build_timeline(
            records,
            filter_,
            calculate_durations=kwargs.get("show_duration", False),
        )

        if kwargs.get("summary", False):
            summary = get_timeline_summary(events)
            return FileResult(
                file=str(file_path),
                status="success",
                data=summary.to_dict(),
            )

        return FileResult(
            file=str(file_path),
            status="success",
            data={
                "event_count": len(events),
                "events": [e.to_dict() for e in events],
            },
        )
    except CclogError as e:
        return FileResult(
            file=str(file_path),
            status="error",
            error=e.to_dict(),
        )
    except Exception as e:
        return FileResult(
            file=str(file_path),
            status="error",
            error={"error": "UNEXPECTED_ERROR", "message": str(e)},
        )


CommandType = Literal["info", "search", "tools", "timeline"]


def process_batch(
    files: list[Path],
    command: CommandType,
    args: dict[str, Any] | None = None,
    max_workers: int | None = None,
    fail_fast: bool = False,
) -> BatchResult:
    """
    Process multiple files with a command in parallel.

    Args:
        files: List of file paths to process
        command: Command to run (info, search, tools, timeline)
        args: Command-specific arguments
        max_workers: Maximum parallel workers (default: min(32, cpu_count + 4))
        fail_fast: Stop on first error

    Returns:
        BatchResult with individual file results and summary
    """
    if args is None:
        args = {}

    # Select processor based on command - define typed functions for each processor
    def _process_info(f: Path) -> FileResult:
        return process_file_info(f)

    def _process_search(f: Path) -> FileResult:
        # Extract pattern and pass remaining args
        search_args = {k: v for k, v in args.items() if k != "pattern"}
        return process_file_search(f, args.get("pattern", ""), **search_args)

    def _process_tools(f: Path) -> FileResult:
        return process_file_tools(f, **args)

    def _process_timeline(f: Path) -> FileResult:
        return process_file_timeline(f, **args)

    processors: dict[str, Callable[[Path], FileResult]] = {
        "info": _process_info,
        "search": _process_search,
        "tools": _process_tools,
        "timeline": _process_timeline,
    }

    if command not in processors:
        result = BatchResult()
        for file_path in files:
            result.add_result(
                FileResult(
                    file=str(file_path),
                    status="error",
                    error={
                        "error": "INVALID_COMMAND",
                        "message": f"Unknown batch command: {command}",
                        "valid_commands": list(processors.keys()),
                    },
                )
            )
        return result

    processor = processors[command]
    batch_result = BatchResult()

    # Validate files exist
    valid_files: list[Path] = []
    for file_path in files:
        if not file_path.exists():
            batch_result.add_result(
                FileResult(
                    file=str(file_path),
                    status="error",
                    error=FileNotFoundCclogError(str(file_path)).to_dict(),
                )
            )
            if fail_fast:
                return batch_result
        else:
            valid_files.append(file_path)

    # Process files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(processor, f): f for f in valid_files}

        for future in as_completed(futures):
            result = future.result()
            batch_result.add_result(result)

            if fail_fast and result.status == "error":
                # Cancel remaining futures
                for f in futures:
                    f.cancel()
                break

    return batch_result
