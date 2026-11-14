"""Tests for the README generator."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "update_readme.py"

_spec = importlib.util.spec_from_file_location("update_readme", SCRIPT)
assert _spec is not None and _spec.loader is not None
update_readme = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(update_readme)

render_readme = update_readme.render_readme


def test_render_readme_removes_toctree() -> None:
    source = "# Title\n\n```{toctree}\n:hidden:\n\npage\n```\n\nText\n"
    result = render_readme(source)

    assert "{toctree}" not in result
    assert "page" not in result
    assert "Text" in result


def test_render_readme_rewrites_relative_markdown_links() -> None:
    source = "# Title\n\n[Snake](games/snake.md) and [Usage](usage/index.md#controls).\n"
    result = render_readme(source)

    assert (
        "[Snake](https://github.com/pamagister/asciicade/blob/main/docs/games/snake.md)" in result
    )
    assert (
        "[Usage](https://github.com/pamagister/asciicade/blob/main/docs/usage/index.md#controls)"
        in result
    )
    assert "](games/snake.md)" not in result


def test_render_readme_keeps_external_links() -> None:
    source = (
        "# Title\n\n"
        "[Textual](https://textual.textualize.io/) and "
        "[LICENSE](https://github.com/pamagister/asciicade/blob/main/LICENSE).\n"
    )
    result = render_readme(source)

    assert "[Textual](https://textual.textualize.io/)" in result
    assert "[LICENSE](https://github.com/pamagister/asciicade/blob/main/LICENSE)" in result


def test_committed_readme_matches_index() -> None:
    source = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")

    assert (ROOT / "README.md").read_text(encoding="utf-8") == render_readme(source)


def test_committed_readme_starts_with_generated_marker() -> None:
    result = (ROOT / "README.md").read_text(encoding="utf-8")

    assert result.startswith(update_readme.PREFIX)


def test_committed_readme_has_no_relative_markdown_links() -> None:
    result = (ROOT / "README.md").read_text(encoding="utf-8")

    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", result):
        target = match.group(1).split("#", 1)[0]
        assert "://" in target or target.startswith("mailto:") or not target.endswith(".md"), (
            f"relative Markdown link in README: {match.group(0)}"
        )
