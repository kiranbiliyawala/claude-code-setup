"""
info command - Display trace metadata and statistics.

Output: JSON object with trace summary
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ptrace.formatters.json import output_json

if TYPE_CHECKING:
    from argparse import Namespace

    from ptrace.index import EventIndex

# Exit codes
EXIT_SUCCESS = 0


def run(index: EventIndex, args: Namespace) -> int:
    """
    Execute the info command.

    Outputs trace metadata and event counts as JSON.

    Args:
        index: EventIndex for the trace
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    summary = index.get_summary()

    # Add additional context from archive
    ctx = index.archive.get_context_options()
    if ctx:
        options = ctx.get("options", {})
        summary["base_url"] = options.get("baseURL", "")
        summary["user_agent"] = options.get("userAgent", "")
        summary["locale"] = options.get("locale", "")
        summary["platform"] = ctx.get("platform", "")
        summary["sdk_language"] = ctx.get("sdkLanguage", "")

    # List available resources
    summary["screenshot_count"] = len(index.archive.list_screenshots())
    summary["source_file_count"] = len(index.archive.list_source_files())

    output_json(summary, sys.stdout, pretty=args.pretty)
    return EXIT_SUCCESS
