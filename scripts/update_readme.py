"""Generate ``README.md`` from ``docs/index.md``."""

from __future__ import annotations

from pathlib import Path

SOURCE = Path("docs/index.md")
TARGET = Path("README.md")
PREFIX = "<!-- This README.md is auto-generated from docs/index.md -->\n\n"


def main() -> None:
    """Write the generated README and report the result."""
    source_content = SOURCE.read_text(encoding="utf-8")
    TARGET.write_text(PREFIX + source_content, encoding="utf-8")
    print(f"Generated: {TARGET} updated from {SOURCE}")


if __name__ == "__main__":
    main()