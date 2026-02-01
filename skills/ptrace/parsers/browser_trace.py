"""
Parser for 0-trace.trace file.

Converts browser trace events (console, actions, screenshots, etc.)
into normalized Event objects.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from ptrace.models import ActionEvent, ConsoleEvent, Event, ScreenshotRef

if TYPE_CHECKING:
    from ptrace.archive import TraceArchive


class BrowserTraceParser:
    """
    Parser for browser trace data (0-trace.trace).

    Handles event types:
    - console: Browser console logs
    - before/after: Action pairs (click, fill, expect, etc.)
    - screencast-frame: Screenshot frames
    - log: Playwright internal logs
    - input: User input events
    - frame-snapshot: DOM snapshots (not exposed as events)
    """

    def __init__(self, archive: TraceArchive):
        self.archive = archive
        self._before_events: dict[str, dict[str, Any]] = {}  # callId -> before entry

    def parse(self) -> Iterator[Event]:  # noqa: PLR0912
        """
        Parse all browser trace events.

        Yields:
            Event objects for console, actions, screenshots, logs, and inputs
        """
        console_index = 0
        action_index = 0
        screenshot_index = 0
        log_index = 0
        input_index = 0

        for entry in self.archive.iter_browser_trace():
            event_type = entry.get("type")

            if event_type == "console":
                event = self._parse_console(entry, console_index)
                if event:
                    yield event
                    console_index += 1

            elif event_type == "before":
                # Store before events for pairing with after
                call_id = entry.get("callId", "")
                if call_id:
                    self._before_events[call_id] = entry

            elif event_type == "after":
                # Pair with before event to create action
                call_id = entry.get("callId", "")
                before = self._before_events.get(call_id)
                if before:
                    event = self._parse_action(before, entry, action_index)
                    if event:
                        yield event
                        action_index += 1
                    # Remove processed before event
                    del self._before_events[call_id]

            elif event_type == "screencast-frame":
                event = self._parse_screenshot(entry, screenshot_index)
                if event:
                    yield event
                    screenshot_index += 1

            elif event_type == "log":
                event = self._parse_log(entry, log_index)
                if event:
                    yield event
                    log_index += 1

            elif event_type == "input":
                event = self._parse_input(entry, input_index)
                if event:
                    yield event
                    input_index += 1

    def _parse_console(self, entry: dict[str, Any], index: int) -> Event | None:
        """Parse a console log entry."""
        level = entry.get("messageType", "log")
        text = entry.get("text", "")
        args = entry.get("args", [])
        location = entry.get("location", {})

        console_event = ConsoleEvent(
            level=level,
            text=text,
            args=args,
            source_url=location.get("url", ""),
            line_number=location.get("lineNumber", 0),
            column_number=location.get("columnNumber", 0),
        )

        return Event(
            index=index,
            timestamp_ms=entry.get("time", 0),
            event_type="console",
            subtype=level,
            source_file="0-trace.trace",
            raw=entry,
            console=console_event,
        )

    def _parse_action(
        self,
        before: dict[str, Any],
        after: dict[str, Any],
        index: int,
    ) -> Event | None:
        """Parse a before/after pair into an action event."""
        method = before.get("method", "")
        params = before.get("params", {})

        # Extract selector from params if available
        selector = params.get("selector")

        # Calculate duration
        start_time = before.get("startTime", 0)
        end_time = after.get("endTime", start_time)
        duration_ms = end_time - start_time

        # Get title if available (from test.trace style entries)
        title = before.get("title", "")

        # Check for error in result
        result = after.get("result", {})
        error = None
        if isinstance(result, dict) and result.get("error"):
            error = str(result.get("error"))

        action_event = ActionEvent(
            action=method,
            selector=selector,
            params=params,
            call_id=before.get("callId", ""),
            page_id=before.get("pageId", ""),
            duration_ms=duration_ms,
            title=title,
            error=error,
            before_snapshot=before.get("beforeSnapshot"),
            after_snapshot=after.get("afterSnapshot"),
        )

        return Event(
            index=index,
            timestamp_ms=start_time,
            event_type="action",
            subtype=method,
            source_file="0-trace.trace",
            raw={"before": before, "after": after},
            action=action_event,
        )

    def _parse_screenshot(self, entry: dict[str, Any], index: int) -> Event | None:
        """Parse a screencast-frame entry."""
        sha1 = entry.get("sha1", "")
        if not sha1:
            return None

        screenshot = ScreenshotRef(
            sha1=sha1,
            width=entry.get("width", 0),
            height=entry.get("height", 0),
            resource_path=f"resources/{sha1}",
        )

        return Event(
            index=index,
            timestamp_ms=entry.get("timestamp", 0),
            event_type="screenshot",
            subtype=None,
            source_file="0-trace.trace",
            raw=entry,
            screenshot=screenshot,
        )

    def _parse_log(self, entry: dict[str, Any], index: int) -> Event | None:
        """Parse a Playwright internal log entry."""
        return Event(
            index=index,
            timestamp_ms=entry.get("time", 0),
            event_type="log",
            subtype=None,
            source_file="0-trace.trace",
            raw=entry,
        )

    def _parse_input(self, entry: dict[str, Any], index: int) -> Event | None:
        """Parse a user input event."""
        # Input events don't have explicit timestamps; use callId to correlate
        return Event(
            index=index,
            timestamp_ms=0,  # Will need to be correlated with action
            event_type="input",
            subtype=None,
            source_file="0-trace.trace",
            raw=entry,
        )
