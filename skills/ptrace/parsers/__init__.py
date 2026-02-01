"""
Parsers for different trace file formats.

Each parser converts raw trace data into normalized Event objects.
"""

from ptrace.parsers.browser_trace import BrowserTraceParser
from ptrace.parsers.network import NetworkParser
from ptrace.parsers.test_trace import TestTraceParser

__all__ = [
    "NetworkParser",
    "BrowserTraceParser",
    "TestTraceParser",
]
