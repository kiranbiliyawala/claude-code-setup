"""
Entry point for running ptrace as a module.

Usage:
    python -m ptrace <trace.zip> <command> [options]
"""

import sys

from ptrace.cli import main

if __name__ == "__main__":
    sys.exit(main())
