"""
Command handlers for ptrace CLI.

Each command module provides a run() function that handles
the command execution and output.
"""

from ptrace.commands.actions import run as run_actions
from ptrace.commands.console import run as run_console
from ptrace.commands.correlate import run as run_correlate
from ptrace.commands.errors import run as run_errors
from ptrace.commands.events import run as run_events
from ptrace.commands.info import run as run_info
from ptrace.commands.network import run as run_network
from ptrace.commands.screenshot import run as run_screenshot

__all__ = [
    "run_info",
    "run_events",
    "run_network",
    "run_console",
    "run_actions",
    "run_errors",
    "run_correlate",
    "run_screenshot",
]
