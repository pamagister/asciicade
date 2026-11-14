"""Generate ``README.md`` from ``docs/index.md``."""

from __future__ import annotations

import re
from pathlib import Path

SOURCE = Path("docs/index.md")
TARGET = Path("README.md")
PREFIX = "<!-- This README.md is auto-generated from docs/index.md -->\n\n"
GITHUB_DOCS_URL = "https://github.com/pamagister/asciicade/blob/main/docs"

TOCTREE_RE = re.compile(r"^```\{toctree\}\n.*?\n```\n?", re.MULTILINE | re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _rewrite_markdown_link(match: re.Match[str]) -> str:
    """Rewrite a relative Markdown link to an absolute GitHub URL."""
    label, target = match.groups()
    if "://" in target or target.startswith("mailto:") or target.startswith("#"):
        return match.group(0)

    path, separator, anchor = target.partition("#")
    if not path.endswith(".md"):
        return match.group(0)

    absolute_target = f"{GITHUB_DOCS_URL}/{path.lstrip('./')}"
    if separator:
        absolute_target = f"{absolute_target}#{anchor}"
    return f"[{label}]({absolute_target})"


def render_readme(source: str) -> str:
    """Return the generated README content for the given documentation source."""
    without_toctree = TOCTREE_RE.sub("", source)
    with_absolute_links = MARKDOWN_LINK_RE.sub(_rewrite_markdown_link, without_toctree)
    normalized = re.sub(r"\n{3,}", "\n\n", with_absolute_links)
    return PREFIX + normalized.strip() + "\n"


def main() -> None:
    """Write the generated README and report the result."""
    source_content = SOURCE.read_text(encoding="utf-8")
    TARGET.write_text(render_readme(source_content), encoding="utf-8")
    print(f"Generated: {TARGET} updated from {SOURCE}")


if __name__ == "__main__":
    main()
