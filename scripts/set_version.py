"""Set the package version in ``src/asciicade/__init__.py``."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

VERSION_FILE = Path("src/asciicade/__init__.py")
VERSION_PATTERN = re.compile(r'^__version__ = "[^"]+"$', re.MULTILINE)


def replace_version(text: str, version: str) -> str:
    """Return ``text`` with the package version replaced by ``version``."""
    updated, count = VERSION_PATTERN.subn(f'__version__ = "{version}"', text)
    if count != 1:
        raise ValueError(f"expected exactly one version line, found {count}")
    return updated


def main() -> None:
    """Update the package version from a command-line argument."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="new package version, for example 0.2.1")
    args = parser.parse_args()

    text = VERSION_FILE.read_text(encoding="utf-8")
    updated = replace_version(text, args.version)
    if updated != text:
        VERSION_FILE.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
