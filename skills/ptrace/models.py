"""
Data models for normalized trace events.

All events from trace files are normalized into a unified Event type with
type-specific payloads. Timestamps are normalized to milliseconds from trace start.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class NetworkEvent:
    """Network request/response data."""

    method: str
    url: str
    status: int
    status_text: str
    duration_ms: float
    request_headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)
    request_body: Any | None = None
    response_body: Any | None = None
    response_content_type: str = ""
    request_body_size: int = 0
    response_body_size: int = 0
    query_string: dict[str, str] = field(default_factory=dict)
    server_ip: str = ""
    timings: dict[str, float] = field(default_factory=dict)


@dataclass
class ConsoleEvent:
    """Browser console log entry."""

    level: str  # debug, log, info, warn, error
    text: str
    args: list[Any] = field(default_factory=list)
    source_url: str = ""
    line_number: int = 0
    column_number: int = 0


@dataclass
class ActionEvent:
    """Playwright action (click, fill, expect, etc.)."""

    action: str  # click, fill, goto, expect, etc.
    selector: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    call_id: str = ""
    page_id: str = ""
    duration_ms: float = 0
    title: str = ""
    error: str | None = None
    before_snapshot: str | None = None
    after_snapshot: str | None = None


@dataclass
class ErrorEvent:
    """Test failure or error."""

    message: str
    stack: list[dict[str, Any]] = field(default_factory=list)
    source: str = ""  # test.trace or 0-trace.trace
    expected: str | None = None
    received: str | None = None


@dataclass
class ScreenshotRef:
    """Reference to a screenshot in the trace resources."""

    sha1: str
    width: int
    height: int
    resource_path: str = ""


EventType = Literal["network", "console", "action", "error", "screenshot", "log", "input"]


@dataclass
class Event:
    """
    Normalized event from any trace source.

    All events are normalized to a common format with:
    - Unified timestamp (ms from trace start)
    - Event type classification
    - Type-specific payload in corresponding field
    """

    index: int
    timestamp_ms: float  # Relative to trace start
    event_type: EventType
    subtype: str | None = None  # GET, POST, error, warn, click, fill, etc.
    source_file: str = ""  # test.trace, 0-trace.trace, 0-trace.network
    raw: dict[str, Any] = field(default_factory=dict)

    # Type-specific payloads (only one will be set based on event_type)
    network: NetworkEvent | None = None
    console: ConsoleEvent | None = None
    action: ActionEvent | None = None
    error: ErrorEvent | None = None
    screenshot: ScreenshotRef | None = None

    # For log and input events, data is stored in raw

    def to_dict(self, include_raw: bool = False) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "index": self.index,
            "timestamp_ms": self.timestamp_ms,
            "event_type": self.event_type,
        }

        if self.subtype:
            result["subtype"] = self.subtype

        if include_raw:
            result["source_file"] = self.source_file
            result["raw"] = self.raw

        # Add type-specific payload
        if self.network:
            result["network"] = _network_to_dict(self.network)
        elif self.console:
            result["console"] = _console_to_dict(self.console)
        elif self.action:
            result["action"] = _action_to_dict(self.action)
        elif self.error:
            result["error"] = _error_to_dict(self.error)
        elif self.screenshot:
            result["screenshot"] = _screenshot_to_dict(self.screenshot)
        elif self.event_type in ("log", "input"):
            # For log and input, extract relevant fields from raw
            result["data"] = self.raw

        return result


def _network_to_dict(n: NetworkEvent) -> dict[str, Any]:
    """Convert NetworkEvent to dict."""
    return {
        "method": n.method,
        "url": n.url,
        "status": n.status,
        "status_text": n.status_text,
        "duration_ms": n.duration_ms,
        "request_headers": n.request_headers,
        "response_headers": n.response_headers,
        "request_body": n.request_body,
        "response_body": n.response_body,
        "response_content_type": n.response_content_type,
        "request_body_size": n.request_body_size,
        "response_body_size": n.response_body_size,
        "query_string": n.query_string,
        "server_ip": n.server_ip,
        "timings": n.timings,
    }


def _console_to_dict(c: ConsoleEvent) -> dict[str, Any]:
    """Convert ConsoleEvent to dict."""
    return {
        "level": c.level,
        "text": c.text,
        "args": c.args,
        "source_url": c.source_url,
        "line_number": c.line_number,
        "column_number": c.column_number,
    }


def _action_to_dict(a: ActionEvent) -> dict[str, Any]:
    """Convert ActionEvent to dict."""
    return {
        "action": a.action,
        "selector": a.selector,
        "params": a.params,
        "call_id": a.call_id,
        "page_id": a.page_id,
        "duration_ms": a.duration_ms,
        "title": a.title,
        "error": a.error,
        "before_snapshot": a.before_snapshot,
        "after_snapshot": a.after_snapshot,
    }


def _error_to_dict(e: ErrorEvent) -> dict[str, Any]:
    """Convert ErrorEvent to dict."""
    return {
        "message": e.message,
        "stack": e.stack,
        "source": e.source,
        "expected": e.expected,
        "received": e.received,
    }


def _screenshot_to_dict(s: ScreenshotRef) -> dict[str, Any]:
    """Convert ScreenshotRef to dict."""
    return {
        "sha1": s.sha1,
        "width": s.width,
        "height": s.height,
        "resource_path": s.resource_path,
    }
