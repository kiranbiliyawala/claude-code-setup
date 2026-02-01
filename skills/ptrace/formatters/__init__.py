"""
Output formatters for ptrace commands.

Supports JSON, JSONL, and table output formats.
"""

from ptrace.formatters.json import output_json, output_jsonl
from ptrace.formatters.table import output_table

__all__ = [
    "output_json",
    "output_jsonl",
    "output_table",
]
