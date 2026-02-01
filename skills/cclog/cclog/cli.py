"""CLI entrypoint for cclog."""

from __future__ import annotations

import sys
from typing import Any, Literal, cast

import click
import orjson
from rich.console import Console
from rich.table import Table

from cclog import __version__
from cclog.errors import CclogError, FilterInvalidError, handle_error
from cclog.filters import MessageFilter, apply_filters
from cclog.parser import get_file_info, parse_jsonl
from cclog.search import SearchFilter, search_content
from cclog.subagents import (
    build_subagent_tree,
    extract_subagents,
    find_parent_session,
    find_project_dir_from_file,
    find_session_files,
)
from cclog.timeline import TimelineFilter, build_timeline, get_timeline_summary, group_events
from cclog.tools import ToolFilter, get_tools

# Import exporters lazily to avoid circular imports
ExporterType = Literal["markdown", "csv", "simple-json", "llm"]

console = Console()


class OutputFormat:
    """Output format handler."""

    def __init__(self, format_type: str = "json", quiet: bool = False) -> None:
        self.format_type = format_type
        self.quiet = quiet

    def output(self, data: Any) -> None:
        """Output data in the configured format."""
        if self.quiet:
            return

        if self.format_type == "json":
            self._output_json(data)
        elif self.format_type == "human":
            self._output_human(data)
        elif self.format_type == "ndjson":
            self._output_ndjson(data)

    def _output_json(self, data: Any) -> None:
        """Output as formatted JSON."""
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")
        output = orjson.dumps(data, option=orjson.OPT_INDENT_2)
        sys.stdout.buffer.write(output)
        sys.stdout.buffer.write(b"\n")

    def _output_ndjson(self, data: Any) -> None:
        """Output as newline-delimited JSON (for streaming)."""
        items: list[Any] = cast(list[Any], data) if isinstance(data, list) else [data]
        for item_data in items:
            if hasattr(item_data, "model_dump"):
                item_data = item_data.model_dump(mode="json")
            output = orjson.dumps(item_data)
            sys.stdout.buffer.write(output)
            sys.stdout.buffer.write(b"\n")

    def _output_human(self, data: Any) -> None:
        """Output as human-readable table."""
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")

        if isinstance(data, dict):
            self._output_dict_as_table(data)  # type: ignore[arg-type]
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            self._output_list_as_table(data)  # type: ignore[arg-type]
        else:
            console.print(data)

    def _output_dict_as_table(self, data: dict[str, Any]) -> None:
        """Output a dict as a key-value table."""
        table = Table(show_header=True, header_style="bold")
        table.add_column("Field")
        table.add_column("Value")

        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value_str = orjson.dumps(value).decode()
            else:
                value_str = str(value) if value is not None else "-"
            table.add_row(key, value_str)

        console.print(table)

    def _output_list_as_table(self, data: list[dict[str, Any]]) -> None:
        """Output a list as a table."""
        if not data:
            console.print("[dim]No results[/dim]")
            return

        # Get headers from first item
        first = data[0]
        headers: list[str] = list(first.keys())
        table = Table(show_header=True, header_style="bold")
        for h in headers:
            table.add_column(str(h))
        for item in data:
            row = [str(item.get(h, "-")) for h in headers]
            table.add_row(*row)
        console.print(table)


# Global options passed via context
pass_output = click.make_pass_decorator(OutputFormat, ensure=True)


@click.group()
@click.option(
    "--format",
    "format_type",
    type=click.Choice(["json", "human", "ndjson"]),
    default="json",
    help="Output format (default: json)",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress output")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.version_option(
    version=__version__,
    prog_name="cclog",
    message='{"version": "%(version)s", "features": ["info", "messages", "tools"]}',
)
@click.pass_context
def main(
    ctx: click.Context,
    format_type: str,
    quiet: bool,
    verbose: bool,  # noqa: ARG001
) -> None:
    """
    Agent-native CLI for reading Claude Code JSONL conversation files.

    All commands output JSON by default. Use --format=human for tables.

    Global options (--format, --quiet, --verbose) must appear BEFORE the command:

    \b
      cclog --format=human info file.jsonl    # Correct
      cclog info --format=human file.jsonl    # Wrong - unknown option
    """
    ctx.ensure_object(dict)
    ctx.obj = OutputFormat(format_type=format_type, quiet=quiet)


@main.command()
@click.argument("file", type=click.Path(exists=False))
@pass_output
def info(output: OutputFormat, file: str) -> None:
    """
    Get metadata about a conversation file.

    Returns session ID, size, record counts, tool usage, and time range
    without loading the full file content.

    \b
    Example:
        cclog info conversation.jsonl
        cclog info ~/.claude/projects/-path-to-project/abc123.jsonl
    """
    try:
        file_info = get_file_info(file)
        output.output(file_info)
    except CclogError as e:
        handle_error(e)


@main.command()
@click.argument("file", type=click.Path(exists=False))
@click.option("--role", type=click.Choice(["user", "assistant"]), help="Filter by role")
@click.option(
    "--content-type",
    type=click.Choice(["thinking", "text", "tool_use", "tool_result"]),
    help="Filter by content type",
)
@click.option("--tool", "tool_name", help="Filter by tool name")
@click.option("--limit", type=int, help="Maximum number of messages to return")
@click.option("--offset", type=int, default=0, help="Number of messages to skip")
@pass_output
def messages(
    output: OutputFormat,
    file: str,
    role: str | None,
    content_type: str | None,
    tool_name: str | None,
    limit: int | None,
    offset: int,
) -> None:
    """
    Extract messages with filtering.

    Streams messages as NDJSON by default. Use --format=json for array output.

    \b
    Examples:
        cclog messages conversation.jsonl
        cclog messages conversation.jsonl --role=assistant
        cclog messages conversation.jsonl --content-type=tool_use --tool=Task
        cclog messages conversation.jsonl --limit=10 --offset=5
    """
    try:
        filter_ = MessageFilter(
            role=role,
            content_type=content_type,
            tool_name=tool_name,
            limit=limit,
            offset=offset,
        )

        records = parse_jsonl(file)
        filtered = apply_filters(records, filter_)

        # Collect for json/human output, stream for ndjson
        if output.format_type == "ndjson":
            for record in filtered:
                output.output(record)
        else:
            results = [r.model_dump(mode="json") for r in filtered]
            output.output(results)

    except CclogError as e:
        handle_error(e)


@main.command()
@click.argument("file", type=click.Path(exists=False))
@click.option("--name", "tool_name", help="Filter by tool name")
@click.option("--subagent-type", help="Filter Task calls by subagent type")
@click.option(
    "--status",
    type=click.Choice(["success", "error"]),
    help="Filter by result status",
)
@click.option("--limit", type=int, help="Maximum number of tool calls to return")
@click.option("--offset", type=int, default=0, help="Number of tool calls to skip")
@click.option("--full", is_flag=True, help="Include complete input/output (default: truncated)")
@pass_output
def tools(
    output: OutputFormat,
    file: str,
    tool_name: str | None,
    subagent_type: str | None,
    status: str | None,
    limit: int | None,
    offset: int,
    full: bool,
) -> None:
    """
    Extract tool calls with their results.

    Pairs tool_use blocks with their corresponding tool_result.
    Streams as NDJSON by default.

    \b
    Examples:
        cclog tools conversation.jsonl
        cclog tools conversation.jsonl --name=Task
        cclog tools conversation.jsonl --name=Task --subagent-type=general-purpose
        cclog tools conversation.jsonl --status=error
        cclog tools conversation.jsonl --full
    """
    try:
        # Validate subagent-type is only used with Task
        if subagent_type is not None and tool_name is not None and tool_name != "Task":
            raise FilterInvalidError(
                "--subagent-type",
                ["Can only be used with --name=Task or without --name filter"],
            )

        filter_ = ToolFilter(
            name=tool_name,
            subagent_type=subagent_type,
            status=status,
            limit=limit,
            offset=offset,
        )

        tool_calls = get_tools(file, filter_=filter_, full=full)

        if output.format_type == "ndjson":
            for tool_call in tool_calls:
                output.output(tool_call)
        else:
            results = list(tool_calls)
            output.output(results)

    except CclogError as e:
        handle_error(e)


@main.command()
@click.argument("file", type=click.Path(exists=False))
@click.argument("pattern")
@click.option(
    "--in",
    "scope",
    type=click.Choice(["text", "thinking", "tool_input", "tool_result", "all"]),
    default="all",
    help="Where to search (default: all)",
)
@click.option("--regex", "-r", is_flag=True, help="Treat pattern as regex")
@click.option("--ignore-case", "-i", is_flag=True, help="Case insensitive search")
@click.option("--context", "-C", "context_lines", type=int, default=0, help="Lines of context")
@click.option("--limit", type=int, help="Maximum number of matches to return")
@click.option("--offset", type=int, default=0, help="Number of matches to skip")
@pass_output
def search(
    output: OutputFormat,
    file: str,
    pattern: str,
    scope: str,
    regex: bool,
    ignore_case: bool,
    context_lines: int,
    limit: int | None,
    offset: int,
) -> None:
    """
    Full-text search across conversation content.

    Searches in text, thinking, tool inputs, and tool results.
    Use --in to limit search to specific content types.

    \b
    Examples:
        cclog search conversation.jsonl "validation error"
        cclog search conversation.jsonl "error" --in=tool_result
        cclog search conversation.jsonl "\\d{3}" --regex -i
        cclog search conversation.jsonl "TODO" --context=2
    """
    try:
        filter_ = SearchFilter(
            pattern=pattern,
            scope=scope,  # type: ignore[arg-type]
            regex=regex,
            case_insensitive=ignore_case,
            context_lines=context_lines,
            limit=limit,
            offset=offset,
        )

        records = parse_jsonl(file)
        matches = search_content(records, filter_)

        if output.format_type == "ndjson":
            for match in matches:
                output.output(match.to_dict())
        else:
            results = [m.to_dict() for m in matches]
            output.output(results)

    except CclogError as e:
        handle_error(e)


@main.command()
@click.argument("file", type=click.Path(exists=False), required=False)
@click.option("--session", "session_id", help="Find files by session ID")
@click.option("--tree", is_flag=True, help="Show hierarchical tree view")
@click.option("--find-parent", is_flag=True, help="Find parent session of subagent file")
@click.option("--limit", type=int, help="Maximum number of subagents to return")
@click.option("--offset", type=int, default=0, help="Number of subagents to skip")
@pass_output
def subagents(
    output: OutputFormat,
    file: str | None,
    session_id: str | None,
    tree: bool,
    find_parent: bool,
    limit: int | None,
    offset: int,
) -> None:
    """
    Find and list subagent sessions.

    Discovers Task tool invocations and their corresponding subagent files.
    Use --tree for hierarchical view of parent -> subagent relationships.

    \b
    Examples:
        cclog subagents conversation.jsonl
        cclog subagents conversation.jsonl --tree
        cclog subagents agent-a3f5885.jsonl --find-parent
        cclog subagents --session=bba90b61-ff9e-4bf6-a3a8-43f13edf0c11
    """
    try:
        if find_parent:
            if not file:
                raise FilterInvalidError("--find-parent", ["Requires a file argument"])
            parent = find_parent_session(file)
            if parent:
                output.output({"parent_file": str(parent)})
            else:
                output.output({"parent_file": None, "message": "No parent session found"})
            return

        if session_id:
            # Find all files for a session
            from pathlib import Path

            # Determine project directory
            if file:
                project_dir = find_project_dir_from_file(file)
            else:
                # Use home directory default
                project_dir = Path.home() / ".claude" / "projects"
                # Try to find the session in any project
                for proj in project_dir.iterdir():
                    if proj.is_dir():
                        test_file = proj / f"{session_id}.jsonl"
                        if test_file.exists():
                            project_dir = proj
                            break

            if project_dir and project_dir.exists():
                files = find_session_files(project_dir, session_id)
                output.output({"session_id": session_id, "files": [str(f) for f in files]})
            else:
                result: dict[str, str | list[str]] = {
                    "session_id": session_id,
                    "files": [],
                    "message": "Project not found",
                }
                output.output(result)
            return

        if not file:
            raise FilterInvalidError("file", ["Either file or --session is required"])

        if tree:
            # Build full tree
            subagent_tree = build_subagent_tree(file)
            output.output(subagent_tree.to_dict())
        else:
            # List subagents
            project_dir = find_project_dir_from_file(file)
            records = parse_jsonl(file)
            subagent_list = list(extract_subagents(records, project_dir))

            # Apply pagination
            start = offset
            end = offset + limit if limit else None
            paginated = subagent_list[start:end]

            if output.format_type == "ndjson":
                for subagent in paginated:
                    output.output(subagent.to_dict())
            else:
                output.output([s.to_dict() for s in paginated])

    except CclogError as e:
        handle_error(e)


@main.command()
@click.argument("file", type=click.Path(exists=False))
@click.option("--after", help="Show events after this timestamp (ISO format)")
@click.option("--before", help="Show events before this timestamp (ISO format)")
@click.option(
    "--event-type",
    "event_types",
    multiple=True,
    type=click.Choice(["user_message", "thinking", "text", "tool_use", "tool_result"]),
    help="Filter by event type (can specify multiple)",
)
@click.option(
    "--tool", "tool_names", multiple=True, help="Filter by tool name (can specify multiple)"
)
@click.option(
    "--group-by",
    type=click.Choice(["tool", "event_type"]),
    help="Group events by tool or event_type",
)
@click.option("--show-duration", is_flag=True, help="Include duration between events")
@click.option("--summary", is_flag=True, help="Show summary statistics only")
@click.option("--limit", type=int, help="Maximum number of events to return")
@click.option("--offset", type=int, default=0, help="Number of events to skip")
@pass_output
def timeline(
    output: OutputFormat,
    file: str,
    after: str | None,
    before: str | None,
    event_types: tuple[str, ...],
    tool_names: tuple[str, ...],
    group_by: str | None,
    show_duration: bool,
    summary: bool,
    limit: int | None,
    offset: int,
) -> None:
    """
    Show event timeline from a conversation.

    Extracts events from messages and shows them in chronological order
    with optional duration calculation between events.

    \b
    Examples:
        cclog timeline conversation.jsonl
        cclog timeline conversation.jsonl --show-duration
        cclog timeline conversation.jsonl --event-type=tool_use --tool=Task
        cclog timeline conversation.jsonl --group-by=tool
        cclog timeline conversation.jsonl --summary
    """
    from datetime import datetime

    from cclog.errors import TimestampParseError

    try:
        # Parse timestamps
        after_dt = None
        before_dt = None

        if after:
            try:
                after_dt = datetime.fromisoformat(after)
            except ValueError:
                raise TimestampParseError(after) from None

        if before:
            try:
                before_dt = datetime.fromisoformat(before)
            except ValueError:
                raise TimestampParseError(before) from None

        filter_ = TimelineFilter(
            after=after_dt,
            before=before_dt,
            event_types=list(event_types) if event_types else None,  # type: ignore[arg-type]
            tool_names=list(tool_names) if tool_names else None,
            group_by=group_by,
            limit=limit,
            offset=offset,
        )

        records = parse_jsonl(file)
        events = build_timeline(records, filter_, calculate_durations=show_duration)

        if summary:
            # Output summary statistics only
            summary_data = get_timeline_summary(events)
            output.output(summary_data.to_dict())
        elif group_by:
            # Output grouped events
            grouped = group_events(events)
            grouped_output: dict[str, list[dict[str, Any]]] = {
                key: [e.to_dict() for e in evts] for key, evts in grouped.items()
            }
            output.output(grouped_output)
        elif output.format_type == "ndjson":
            for event in events:
                output.output(event.to_dict())
        else:
            output.output([e.to_dict() for e in events])

    except CclogError as e:
        handle_error(e)


@main.command(name="export")
@click.argument("file", type=click.Path(exists=False))
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["markdown", "csv", "simple-json", "llm"]),
    default="markdown",
    help="Export format (default: markdown)",
)
@click.option(
    "--content",
    type=click.Choice(["all", "messages", "tools", "thinking"]),
    default="all",
    help="What content to include (default: all)",
)
@click.option("--max-tokens", type=int, help="Token budget for LLM export")
@click.option("--no-thinking", is_flag=True, help="Exclude thinking blocks")
@click.option("--no-tools", is_flag=True, help="Exclude tool input/output")
@click.option("--truncate", type=int, help="Truncate content at N characters")
@click.option(
    "-o", "--output", "output_file", type=click.Path(), help="Write to file instead of stdout"
)
@pass_output
def export_cmd(
    output: OutputFormat,
    file: str,
    export_format: str,
    content: str,
    max_tokens: int | None,
    no_thinking: bool,
    no_tools: bool,
    truncate: int | None,
    output_file: str | None,
) -> None:
    """
    Export conversation to various formats.

    Converts conversation data to human-readable or machine-optimized formats.
    Use --format=llm with --max-tokens for context-window-aware export.

    \b
    Examples:
        cclog export conversation.jsonl --format=markdown
        cclog export conversation.jsonl --format=csv -o tools.csv
        cclog export conversation.jsonl --format=llm --max-tokens=25000
        cclog export conversation.jsonl --format=simple-json --no-thinking
    """
    from cclog.exporters import CsvExporter, LlmExporter, MarkdownExporter, SimpleJsonExporter
    from cclog.exporters.base import ExportConfig

    try:
        # Build config
        config = ExportConfig(
            content=content,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            include_thinking=not no_thinking,
            include_tool_content=not no_tools,
            truncate_length=truncate,
        )

        # Select exporter
        exporter_map = {
            "markdown": MarkdownExporter,
            "csv": CsvExporter,
            "simple-json": SimpleJsonExporter,
            "llm": LlmExporter,
        }
        exporter_class = exporter_map[export_format]
        exporter = exporter_class(config)

        # Parse and export
        records = parse_jsonl(file)
        result = exporter.export(records)

        # Output
        if output_file:
            with open(output_file, "w") as f:
                f.write(result)
            if not output.quiet:
                msg = f'{{"exported_to": "{output_file}", "format": "{export_format}"}}\n'
                sys.stdout.write(msg)
        else:
            sys.stdout.write(result)
            if not result.endswith("\n"):
                sys.stdout.write("\n")

    except CclogError as e:
        handle_error(e)


@main.group()
@click.pass_context
def batch(ctx: click.Context) -> None:
    """
    Process multiple conversation files in parallel.

    Batch operations run commands across multiple files concurrently.
    Use --project to auto-discover files or --files for explicit list.

    \b
    Examples:
        cclog batch info --project=/path/to/project
        cclog batch search "error" --files='["file1.jsonl", "file2.jsonl"]'
        cclog batch tools --project=/path/to/project --fail-fast
    """
    pass


# Add batch group to main
main.add_command(batch)


def _parse_files_arg(files: str | None) -> list[str] | None:
    """Parse the --files JSON array argument."""
    if not files:
        return None
    import json

    try:
        parsed: Any = json.loads(files)
        if not isinstance(parsed, list):
            raise ValueError("--files must be a JSON array")
        # Validate all elements are strings
        result: list[str] = []
        for item in cast(list[Any], parsed):
            if not isinstance(item, str):
                raise ValueError("All file paths must be strings")
            result.append(item)
        return result
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON: {e}") from e


@batch.command(name="info")
@click.option("--project", help="Project path to auto-discover files from")
@click.option("--files", "files_json", help="JSON array of file paths")
@click.option("--workers", type=int, help="Maximum parallel workers")
@click.option("--fail-fast", is_flag=True, help="Stop on first error")
@pass_output
def batch_info(
    output: OutputFormat,
    project: str | None,
    files_json: str | None,
    workers: int | None,
    fail_fast: bool,
) -> None:
    """
    Get metadata about multiple conversation files.

    \b
    Examples:
        cclog batch info --project=/path/to/project
        cclog batch info --files='["file1.jsonl", "file2.jsonl"]'
    """
    from cclog.batch import discover_files, process_batch

    try:
        files_list = _parse_files_arg(files_json)
        file_paths = discover_files(project=project, files=files_list)

        if not file_paths:
            output.output({"error": "NO_FILES", "message": "No files to process"})
            return

        result = process_batch(
            files=file_paths,
            command="info",
            max_workers=workers,
            fail_fast=fail_fast,
        )
        output.output(result.to_dict())

    except CclogError as e:
        handle_error(e)


@batch.command(name="search")
@click.argument("pattern")
@click.option("--project", help="Project path to auto-discover files from")
@click.option("--files", "files_json", help="JSON array of file paths")
@click.option(
    "--in",
    "scope",
    type=click.Choice(["text", "thinking", "tool_input", "tool_result", "all"]),
    default="all",
    help="Where to search (default: all)",
)
@click.option("--regex", "-r", is_flag=True, help="Treat pattern as regex")
@click.option("--ignore-case", "-i", is_flag=True, help="Case insensitive search")
@click.option("--limit", type=int, help="Maximum matches per file")
@click.option("--workers", type=int, help="Maximum parallel workers")
@click.option("--fail-fast", is_flag=True, help="Stop on first error")
@pass_output
def batch_search(
    output: OutputFormat,
    pattern: str,
    project: str | None,
    files_json: str | None,
    scope: str,
    regex: bool,
    ignore_case: bool,
    limit: int | None,
    workers: int | None,
    fail_fast: bool,
) -> None:
    """
    Search across multiple conversation files.

    \b
    Examples:
        cclog batch search "error" --project=/path/to/project
        cclog batch search "validation" --files='["f1.jsonl", "f2.jsonl"]' -i
    """
    from cclog.batch import discover_files, process_batch

    try:
        files_list = _parse_files_arg(files_json)
        file_paths = discover_files(project=project, files=files_list)

        if not file_paths:
            output.output({"error": "NO_FILES", "message": "No files to process"})
            return

        result = process_batch(
            files=file_paths,
            command="search",
            args={
                "pattern": pattern,
                "scope": scope,
                "regex": regex,
                "case_insensitive": ignore_case,
                "limit": limit,
            },
            max_workers=workers,
            fail_fast=fail_fast,
        )
        output.output(result.to_dict())

    except CclogError as e:
        handle_error(e)


@batch.command(name="tools")
@click.option("--project", help="Project path to auto-discover files from")
@click.option("--files", "files_json", help="JSON array of file paths")
@click.option("--name", "tool_name", help="Filter by tool name")
@click.option("--subagent-type", help="Filter Task calls by subagent type")
@click.option(
    "--status",
    type=click.Choice(["success", "error"]),
    help="Filter by result status",
)
@click.option("--limit", type=int, help="Maximum tool calls per file")
@click.option("--workers", type=int, help="Maximum parallel workers")
@click.option("--fail-fast", is_flag=True, help="Stop on first error")
@pass_output
def batch_tools(
    output: OutputFormat,
    project: str | None,
    files_json: str | None,
    tool_name: str | None,
    subagent_type: str | None,
    status: str | None,
    limit: int | None,
    workers: int | None,
    fail_fast: bool,
) -> None:
    """
    Extract tool calls from multiple conversation files.

    \b
    Examples:
        cclog batch tools --project=/path/to/project
        cclog batch tools --name=Task --project=/path/to/project
    """
    from cclog.batch import discover_files, process_batch

    try:
        files_list = _parse_files_arg(files_json)
        file_paths = discover_files(project=project, files=files_list)

        if not file_paths:
            output.output({"error": "NO_FILES", "message": "No files to process"})
            return

        result = process_batch(
            files=file_paths,
            command="tools",
            args={
                "name": tool_name,
                "subagent_type": subagent_type,
                "status": status,
                "limit": limit,
            },
            max_workers=workers,
            fail_fast=fail_fast,
        )
        output.output(result.to_dict())

    except CclogError as e:
        handle_error(e)


@batch.command(name="timeline")
@click.option("--project", help="Project path to auto-discover files from")
@click.option("--files", "files_json", help="JSON array of file paths")
@click.option(
    "--event-type",
    "event_types",
    multiple=True,
    type=click.Choice(["user_message", "thinking", "text", "tool_use", "tool_result"]),
    help="Filter by event type",
)
@click.option("--tool", "tool_names", multiple=True, help="Filter by tool name")
@click.option("--summary", is_flag=True, help="Show summary statistics only")
@click.option("--limit", type=int, help="Maximum events per file")
@click.option("--workers", type=int, help="Maximum parallel workers")
@click.option("--fail-fast", is_flag=True, help="Stop on first error")
@pass_output
def batch_timeline(
    output: OutputFormat,
    project: str | None,
    files_json: str | None,
    event_types: tuple[str, ...],
    tool_names: tuple[str, ...],
    summary: bool,
    limit: int | None,
    workers: int | None,
    fail_fast: bool,
) -> None:
    """
    Get event timelines from multiple conversation files.

    \b
    Examples:
        cclog batch timeline --project=/path/to/project --summary
        cclog batch timeline --event-type=tool_use --project=/path/to/project
    """
    from cclog.batch import discover_files, process_batch

    try:
        files_list = _parse_files_arg(files_json)
        file_paths = discover_files(project=project, files=files_list)

        if not file_paths:
            output.output({"error": "NO_FILES", "message": "No files to process"})
            return

        result = process_batch(
            files=file_paths,
            command="timeline",
            args={
                "event_types": list(event_types) if event_types else None,
                "tool_names": list(tool_names) if tool_names else None,
                "summary": summary,
                "limit": limit,
            },
            max_workers=workers,
            fail_fast=fail_fast,
        )
        output.output(result.to_dict())

    except CclogError as e:
        handle_error(e)


@main.command()
@click.pass_context
def schema(ctx: click.Context) -> None:
    """
    Output JSON Schema for all command outputs.
    """
    from cclog.models import FileInfo

    output = ctx.obj
    schemas = {
        "info": FileInfo.model_json_schema(),
    }
    output.output(schemas)


@main.command()
@click.pass_context
def capabilities(ctx: click.Context) -> None:
    """
    List available capabilities and features.
    """
    output = ctx.obj
    caps = {
        "commands": [
            "info",
            "messages",
            "tools",
            "search",
            "subagents",
            "timeline",
            "export",
            "batch",
        ],
        "implemented": [
            "info",
            "messages",
            "tools",
            "search",
            "subagents",
            "timeline",
            "export",
            "batch",
        ],
        "features": ["streaming", "filtering", "batch", "parallel_processing"],
        "version": __version__,
    }
    output.output(caps)


if __name__ == "__main__":
    main()
