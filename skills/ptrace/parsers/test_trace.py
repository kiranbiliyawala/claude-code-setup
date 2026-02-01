"""
Parser for test.trace file.

Converts test runner events (failures, hooks, fixtures, test steps)
into normalized Event objects.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from ptrace.models import ActionEvent, ErrorEvent, Event

if TYPE_CHECKING:
    from ptrace.archive import TraceArchive

# ANSI escape code pattern for stripping colors from error messages
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


class TestTraceParser:
    """
    Parser for test trace data (test.trace).

    Handles event types:
    - context-options: Test configuration (browser, viewport, etc.)
    - before/after: Test step pairs (hooks, fixtures, test actions)
    - error: Test failures with stack traces
    """

    def __init__(self, archive: TraceArchive):
        self.archive = archive
        self._before_events: dict[str, dict[str, Any]] = {}  # callId/stepId -> before

    def parse(self) -> Iterator[Event]:
        """
        Parse all test trace events.

        Yields:
            Event objects for test steps and errors
        """
        action_index = 0
        error_index = 0

        for entry in self.archive.iter_test_trace():
            event_type = entry.get("type")

            if event_type == "before":
                # Store before events for pairing with after
                step_id = entry.get("stepId") or entry.get("callId", "")
                if step_id:
                    self._before_events[step_id] = entry

            elif event_type == "after":
                # Pair with before event
                step_id = entry.get("stepId") or entry.get("callId", "")
                before = self._before_events.get(step_id)
                if before:
                    event = self._parse_test_action(before, entry, action_index)
                    if event:
                        yield event
                        action_index += 1
                    del self._before_events[step_id]

            elif event_type == "error":
                event = self._parse_error(entry, error_index)
                if event:
                    yield event
                    error_index += 1

    def parse_errors_only(self) -> Iterator[Event]:
        """
        Parse only error events from test trace.

        This is more efficient when you only need errors.
        """
        error_index = 0
        for entry in self.archive.iter_test_trace():
            if entry.get("type") == "error":
                event = self._parse_error(entry, error_index)
                if event:
                    yield event
                    error_index += 1

    def _parse_test_action(
        self,
        before: dict[str, Any],
        after: dict[str, Any],
        index: int,
    ) -> Event | None:
        """Parse a test step (before/after pair)."""
        method = before.get("method", "")
        title = before.get("title", "")
        params = before.get("params", {})

        # Calculate duration
        start_time = before.get("startTime", 0)
        end_time = after.get("endTime", start_time)
        duration_ms = end_time - start_time

        action_event = ActionEvent(
            action=method,
            selector=None,
            params=params,
            call_id=before.get("callId") or before.get("stepId", ""),
            page_id="",
            duration_ms=duration_ms,
            title=title,
            error=None,
            before_snapshot=None,
            after_snapshot=None,
        )

        return Event(
            index=index,
            timestamp_ms=start_time,
            event_type="action",
            subtype=method,
            source_file="test.trace",
            raw={"before": before, "after": after},
            action=action_event,
        )

    def _parse_error(self, entry: dict[str, Any], index: int) -> Event | None:
        """
        Parse a test error/failure.

        Error messages may contain ANSI escape codes for colors;
        we strip them for clean output.
        """
        raw_message = entry.get("message", "")
        # Strip ANSI escape codes
        message = ANSI_ESCAPE.sub("", raw_message)

        stack = entry.get("stack", [])

        # Try to extract expected/received from assertion error format
        expected, received = self._parse_assertion(message)

        error_event = ErrorEvent(
            message=message,
            stack=stack,
            source="test.trace",
            expected=expected,
            received=received,
        )

        # Errors don't have explicit timestamps in test.trace
        # Use a high timestamp to sort them at the end of the trace
        return Event(
            index=index,
            timestamp_ms=float("inf"),  # Will be sorted last
            event_type="error",
            subtype="test_failure",
            source_file="test.trace",
            raw=entry,
            error=error_event,
        )

    def _parse_assertion(self, message: str) -> tuple[str | None, str | None]:
        """
        Try to extract expected/received values from assertion error message.

        Playwright assertion errors have format:
        expect(received).toBe(expected) // Object.is equality
        Expected: "foo"
        Received: "bar"
        """
        expected = None
        received = None

        lines = message.split("\n")
        for raw_line in lines:
            stripped = raw_line.strip()
            if stripped.startswith("Expected:"):
                expected = stripped[9:].strip()
            elif stripped.startswith("Received:"):
                received = stripped[9:].strip()

        return expected, received

    def has_errors(self) -> bool:
        """Check if the test trace contains any errors."""
        for entry in self.archive.iter_test_trace():
            if entry.get("type") == "error":
                return True
        return False

    def get_first_error(self) -> Event | None:
        """Get the first error from the test trace, if any."""
        for event in self.parse_errors_only():
            return event
        return None
