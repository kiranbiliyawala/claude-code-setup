"""
ptrace - Playwright Trace Inspector for AI Agents

A CLI tool for extracting and analyzing data from Playwright trace.zip files.
Designed for AI agents with JSON/JSONL output and comprehensive filtering.

Usage:
    python -m ptrace <trace.zip> <command> [options]

Commands:
    info        Trace metadata and statistics
    events      All events (normalized, time-ordered)
    network     Network requests/responses
    console     Console log entries
    actions     Playwright actions (click, fill, etc.)
    errors      Test failures and errors
    screenshot  Extract screenshot at timestamp
    correlate   Events correlated by time window

Exit Codes:
    0  Success (results found)
    1  No results found
    2  Invalid arguments
    3  Trace file not found
    4  Trace parse error
    5  Index out of range
"""

__version__ = "2.0.0"

from ptrace.archive import TraceArchive
from ptrace.index import EventIndex
from ptrace.models import (
    ActionEvent,
    ConsoleEvent,
    ErrorEvent,
    Event,
    NetworkEvent,
    ScreenshotRef,
)

__all__ = [
    "TraceArchive",
    "EventIndex",
    "Event",
    "NetworkEvent",
    "ConsoleEvent",
    "ActionEvent",
    "ErrorEvent",
    "ScreenshotRef",
]
