#!/usr/bin/env python3
"""Get the next available ADR number for a given directory."""

import re
import sys
from pathlib import Path

DEFAULT_DIR = "docs/architecture/decisions"


def get_next_adr_number(adr_dir: str | Path) -> int:
    """Scan directory for existing ADRs and return next available number."""
    adr_path = Path(adr_dir)

    if not adr_path.exists():
        return 1

    # Match files like 0001-something.md, 0042-something.md
    pattern = re.compile(r"^(\d{4})-.*\.md$")

    existing_numbers: set[int] = set()
    for file in adr_path.iterdir():
        if file.is_file():
            match = pattern.match(file.name)
            if match:
                existing_numbers.add(int(match.group(1)))

    if not existing_numbers:
        return 1

    return max(existing_numbers) + 1


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1:
        adr_dir = sys.argv[1]
    else:
        adr_dir = DEFAULT_DIR

    next_num = get_next_adr_number(adr_dir)
    print(f"{next_num:04d}")


if __name__ == "__main__":
    main()
