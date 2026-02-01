"""
TraceArchive - Wrapper around ZipFile for Playwright trace files.

Handles reading trace data files and resolving resource references.
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any


class TraceArchive:
    """
    Wrapper around a Playwright trace.zip file.

    Provides access to:
    - test.trace: Test runner events (fixtures, hooks, test steps, failures)
    - 0-trace.trace: Browser events (actions, console, screenshots, DOM)
    - 0-trace.network: Network calls (HAR-like format)
    - resources/: Binary blobs (screenshots, response bodies, source code)
    """

    def __init__(self, path: Path | str):
        """
        Initialize TraceArchive from a trace.zip file.

        Args:
            path: Path to the trace.zip file

        Raises:
            FileNotFoundError: If trace file doesn't exist
            zipfile.BadZipFile: If file is not a valid zip
        """
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Trace file not found: {self.path}")

        self._zf = zipfile.ZipFile(self.path, "r")
        self._context_options: dict[str, Any] | None = None
        self._trace_start_time: float | None = None

    def close(self) -> None:
        """Close the underlying zip file."""
        self._zf.close()

    def __enter__(self) -> TraceArchive:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def list_files(self) -> list[str]:
        """List all files in the archive."""
        return self._zf.namelist()

    def has_file(self, name: str) -> bool:
        """Check if a file exists in the archive."""
        return name in self._zf.namelist()

    def read_raw(self, name: str) -> bytes:
        """Read raw bytes from a file in the archive."""
        return self._zf.read(name)

    def read_text(self, name: str) -> str:
        """Read text content from a file in the archive."""
        return self._zf.read(name).decode("utf-8")

    def get_resource(self, sha1_or_path: str) -> bytes:
        """
        Get resource content by SHA1 reference or path.

        Args:
            sha1_or_path: Either a SHA1 reference or full resource path

        Returns:
            Raw bytes of the resource
        """
        if sha1_or_path.startswith("resources/"):
            return self._zf.read(sha1_or_path)
        return self._zf.read(f"resources/{sha1_or_path}")

    def get_resource_text(self, sha1_or_path: str) -> str | None:
        """
        Get resource content as text by SHA1 reference.

        Returns None if resource doesn't exist or can't be decoded as UTF-8.
        """
        try:
            return self.get_resource(sha1_or_path).decode("utf-8")
        except (KeyError, UnicodeDecodeError):
            return None

    def iter_test_trace(self) -> Iterator[dict[str, Any]]:
        """
        Iterate over entries in test.trace (NDJSON format).

        Yields test runner events: hooks, fixtures, test steps, errors.
        """
        if not self.has_file("test.trace"):
            return

        content = self.read_text("test.trace")
        for line in content.strip().split("\n"):
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def iter_browser_trace(self) -> Iterator[dict[str, Any]]:
        """
        Iterate over entries in 0-trace.trace (NDJSON format).

        Yields browser events: context-options, before/after actions,
        console, screencast-frame, frame-snapshot, log, input.
        """
        if not self.has_file("0-trace.trace"):
            return

        content = self.read_text("0-trace.trace")
        for line in content.strip().split("\n"):
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def iter_network(self) -> Iterator[dict[str, Any]]:
        """
        Iterate over entries in 0-trace.network (NDJSON format).

        Yields network snapshots in HAR-like format.
        """
        if not self.has_file("0-trace.network"):
            return

        content = self.read_text("0-trace.network")
        for line in content.strip().split("\n"):
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def get_context_options(self) -> dict[str, Any]:
        """
        Get browser context options from the trace.

        Returns configuration like viewport, userAgent, baseURL, etc.
        """
        if self._context_options is not None:
            return self._context_options

        for entry in self.iter_browser_trace():
            if entry.get("type") == "context-options":
                self._context_options = entry
                return entry

        # Return empty if not found
        self._context_options = {}
        return self._context_options

    def get_trace_start_time(self) -> float:
        """
        Get the trace start time (monotonicTime from context-options).

        This is the base time for normalizing all timestamps.
        """
        if self._trace_start_time is not None:
            return self._trace_start_time

        ctx = self.get_context_options()
        start_time = ctx.get("monotonicTime", 0.0)
        self._trace_start_time = start_time
        return start_time

    def get_wall_time(self) -> int:
        """Get the wall clock time (epoch ms) when trace started."""
        ctx = self.get_context_options()
        return ctx.get("wallTime", 0)

    def get_test_name(self) -> str:
        """Get the test name/title from context options."""
        ctx = self.get_context_options()
        return ctx.get("title", "")

    def get_browser_name(self) -> str:
        """Get the browser name used in the test."""
        ctx = self.get_context_options()
        return ctx.get("browserName", "")

    def get_viewport(self) -> dict[str, int]:
        """Get the viewport size."""
        ctx = self.get_context_options()
        options = ctx.get("options", {})
        return options.get("viewport", {"width": 0, "height": 0})

    def list_screenshots(self) -> list[str]:
        """List all screenshot resources in the archive."""
        return [
            name
            for name in self._zf.namelist()
            if name.startswith("resources/page@") and name.endswith(".jpeg")
        ]

    def list_source_files(self) -> list[str]:
        """List all source file resources in the archive."""
        return [
            name
            for name in self._zf.namelist()
            if name.startswith("resources/src@") and name.endswith(".txt")
        ]
