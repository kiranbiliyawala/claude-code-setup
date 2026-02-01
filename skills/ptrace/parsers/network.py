"""
Parser for 0-trace.network file.

Converts HAR-like network snapshots into normalized NetworkEvent objects.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ptrace.models import Event, NetworkEvent

if TYPE_CHECKING:
    from ptrace.archive import TraceArchive


class NetworkParser:
    """
    Parser for network trace data (0-trace.network).

    Converts resource-snapshot entries into NetworkEvent objects.
    """

    def __init__(self, archive: TraceArchive):
        self.archive = archive
        self._trace_start_epoch_ms: int | None = None

    def _get_trace_start_epoch(self) -> int:
        """Get trace start time in epoch milliseconds."""
        if self._trace_start_epoch_ms is None:
            self._trace_start_epoch_ms = self.archive.get_wall_time()
        return self._trace_start_epoch_ms

    def parse(self) -> Iterator[Event]:
        """
        Parse all network events from the trace.

        Yields:
            Event objects with network payload
        """
        index = 0
        for entry in self.archive.iter_network():
            event = self._parse_entry(entry, index)
            if event:
                yield event
                index += 1

    def _parse_entry(self, entry: dict[str, Any], index: int) -> Event | None:
        """Parse a single network entry into an Event."""
        if entry.get("type") != "resource-snapshot":
            return None

        snapshot = entry.get("snapshot", {})
        request = snapshot.get("request", {})
        response = snapshot.get("response", {})

        # Parse timestamp
        timestamp_ms = self._parse_timestamp(snapshot)

        # Parse headers into dict format
        request_headers = self._headers_to_dict(request.get("headers", []))
        response_headers = self._headers_to_dict(response.get("headers", []))

        # Parse query string
        query_string = self._query_to_dict(request.get("queryString", []))

        # Get content type
        content_type = self._get_content_type(response_headers)

        # Parse bodies
        request_body = self._parse_body(
            request.get("postData", {}),
            self._get_content_type(request_headers),
        )
        response_body = self._parse_body(
            response.get("content", {}),
            content_type,
        )

        # Calculate body sizes
        request_body_size = request.get("bodySize", 0)
        response_body_size = response.get("bodySize", 0)

        # Parse timings
        raw_timings = snapshot.get("timings", {})
        timings = {
            "dns": raw_timings.get("dns", 0),
            "connect": raw_timings.get("connect", 0),
            "ssl": raw_timings.get("ssl", 0),
            "send": raw_timings.get("send", 0),
            "wait": raw_timings.get("wait", 0),
            "receive": raw_timings.get("receive", 0),
        }
        duration_ms = snapshot.get("time", 0)

        method = request.get("method", "GET")

        network_event = NetworkEvent(
            method=method,
            url=request.get("url", ""),
            status=response.get("status", 0),
            status_text=response.get("statusText", ""),
            duration_ms=duration_ms,
            request_headers=request_headers,
            response_headers=response_headers,
            request_body=request_body,
            response_body=response_body,
            response_content_type=content_type,
            request_body_size=request_body_size,
            response_body_size=response_body_size,
            query_string=query_string,
            server_ip=snapshot.get("serverIPAddress", ""),
            timings=timings,
        )

        return Event(
            index=index,
            timestamp_ms=timestamp_ms,
            event_type="network",
            subtype=method,
            source_file="0-trace.network",
            raw=entry,
            network=network_event,
        )

    def _parse_timestamp(self, snapshot: dict[str, Any]) -> float:
        """
        Parse timestamp from snapshot.

        Network entries use _monotonicTime or ISO8601 startedDateTime.
        """
        # Prefer monotonicTime if available (already in ms)
        if "_monotonicTime" in snapshot:
            return snapshot["_monotonicTime"]

        # Fall back to parsing startedDateTime
        started = snapshot.get("startedDateTime", "")
        if started:
            try:
                dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                epoch_ms = dt.timestamp() * 1000
                start_epoch = self._get_trace_start_epoch()
                return epoch_ms - start_epoch
            except (ValueError, TypeError):
                pass

        return 0.0

    def _headers_to_dict(self, headers: list[dict[str, str]]) -> dict[str, str]:
        """Convert list of {name, value} headers to dict."""
        return {h.get("name", ""): h.get("value", "") for h in headers if h.get("name")}

    def _query_to_dict(self, query: list[dict[str, str]]) -> dict[str, str]:
        """Convert list of {name, value} query params to dict."""
        return {q.get("name", ""): q.get("value", "") for q in query if q.get("name")}

    def _get_content_type(self, headers: dict[str, str]) -> str:
        """Get content-type from headers dict (case-insensitive)."""
        for key, value in headers.items():
            if key.lower() == "content-type":
                return value
        return ""

    def _parse_body(
        self,
        body_data: dict[str, Any],
        content_type: str,
    ) -> Any | None:
        """
        Parse body content.

        Handles both inline text and SHA1 resource references.
        Parses JSON if content-type is application/json.
        """
        if not body_data:
            return None

        # Get body text
        body_text: str | None = None
        if "_sha1" in body_data:
            body_text = self.archive.get_resource_text(body_data["_sha1"])
        elif "text" in body_data:
            body_text = body_data.get("text")

        if not body_text:
            return None

        # Parse JSON if applicable
        if "application/json" in content_type:
            try:
                return json.loads(body_text)
            except json.JSONDecodeError:
                return body_text

        # Return as-is for other types
        return body_text
