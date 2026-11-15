"""Render game documentation pages from the game registry.

All content comes from ``GameMetadata.docs`` in the game packages; this script
renders deterministic Markdown pages under ``docs/games/`` and synchronizes the
game list in ``docs/index.md`` between ``games:start``/``games:end`` markers.

Usage:
    uv run ./scripts/render_game_docs.py           # write generated files
    uv run ./scripts/render_game_docs.py --check   # fail if output is stale
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

from asciicade.core.game import GameDocs, GameMode
from asciicade.core.options import BooleanOptionDefinition, ChoiceOptionDefinition
from asciicade.core.registry import GameRegistration
from asciicade.games import build_default_registry
from asciicade.ui.preview import render_game_preview

GAMES_DIR = Path("docs/games")
INDEX_FILE = Path("docs/index.md")
INDEX_START_MARKER = "<!-- games:start -->"
INDEX_END_MARKER = "<!-- games:end -->"


def _normalize(body: str) -> str:
    """Return the body as flowing Markdown.

    Bodies carry hard ``\\n`` line breaks (needed for the in-game instructions
    display); the rendered page re-flows them into wrapped paragraphs, keeping
    bullet and table lines as separate blocks. Blank lines separate paragraphs.
    """
    blocks = body.strip().split("\n\n")
    return "\n\n".join(_wrap_paragraph(b) for b in blocks)


def _wrap_paragraph(paragraph: str, width: int = 80) -> str:
    """Re-wrap one Markdown paragraph, preserving bullet and table lines.

    Consecutive ``- `` lines form one bullet item; hard ``\\n`` inside an item
    becomes a space so the item flows as one wrapped block. All remaining
    consecutive text lines are joined into a single wrapped paragraph.
    """
    lines = [line.strip() for line in paragraph.split("\n") if line.strip() != ""]
    out: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            out.append(
                textwrap.fill(
                    " ".join(buffer),
                    width=width,
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
            buffer.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("- "):
            flush()
            item = [line]
            i += 1
            while i < len(lines) and not lines[i].startswith("- ") and not lines[i].startswith("|"):
                item.append(lines[i])
                i += 1
            out.append(
                textwrap.fill(
                    " ".join(item),
                    width=width,
                    subsequent_indent="  ",
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
        elif line.startswith("|"):
            flush()
            out.append(line)
            i += 1
        else:
            buffer.append(line)
            i += 1
    flush()
    return "\n".join(out)


def _render_options(registration: GameRegistration) -> str:
    """Render the options section for a game, or an empty string if it has none."""
    registry = registration.metadata.options
    if registry is None or not registry.definitions:
        return ""
    lines = ["| Option | Values | Default |", "|---|---|---|"]
    for definition in registry.definitions:
        if isinstance(definition, ChoiceOptionDefinition):
            values = ", ".join(definition.values)
            default = definition.default
        elif isinstance(definition, BooleanOptionDefinition):
            values = "On / Off"
            default = "On" if definition.default else "Off"
        else:
            raise TypeError(f"Unknown option definition type: {type(definition)!r}")
        lines.append(f"| {definition.label} | {values} | {default} |")
    return "\n".join(lines)


def _render_sections(docs: GameDocs, registration: GameRegistration) -> str:
    """Render the extra sections, substituting the options table where requested."""
    blocks: list[str] = []
    options_table = _render_options(registration)
    for title, body in docs.sections:
        rendered = _normalize(body)
        if "{options}" in rendered:
            rendered = rendered.replace("{options}", options_table)
        blocks.append(f"## {title}\n\n{rendered}")
    return "\n\n".join(blocks)


def _join_blocks(blocks: list[str]) -> str:
    """Join Markdown blocks with a single blank line between them."""
    return "\n\n".join(block.strip() for block in blocks if block.strip())


def render_page(registration: GameRegistration) -> str:
    """Render one game's documentation page as Markdown."""
    metadata = registration.metadata
    docs = metadata.docs
    parts = [f"# {metadata.name}", _normalize(docs.page_description)]

    preview = render_game_preview(registration)
    if preview:
        parts += ["## Gameplay preview", f"```text\n{preview}\n```"]

    if GameMode.SINGLE_PLAYER in metadata.modes:
        parts += ["## Single player", _normalize(docs.single_player)]
    if GameMode.MULTIPLAYER in metadata.modes and docs.multiplayer:
        parts += ["## Two players", _normalize(docs.multiplayer)]

    sections = _render_sections(docs, registration)
    if sections:
        parts += [sections]

    if docs.controls_long:
        parts += [
            "## Controls",
            f"**Quick:** {docs.controls_short}",
            _normalize(docs.controls_long),
        ]
    else:
        parts += ["## Controls", f"**Quick:** {docs.controls_short}"]

    return _join_blocks(parts) + "\n"


def render_index_games(registrations: tuple[GameRegistration, ...]) -> str:
    """Render the game list block for ``docs/index.md``."""
    lines = []
    for registration in registrations:
        metadata = registration.metadata
        lines.append(
            f"- [{metadata.name}](games/{metadata.identifier}.md) — {metadata.docs.summary}"
        )
    return "\n".join(lines)


def sync_index(index_content: str, registrations: tuple[GameRegistration, ...]) -> str:
    """Replace the marked game list block in the index content."""
    start = index_content.find(INDEX_START_MARKER)
    end = index_content.find(INDEX_END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise ValueError(
            f"docs/index.md must contain '{INDEX_START_MARKER}' before '{INDEX_END_MARKER}'."
        )
    block = render_index_games(registrations)
    return (
        index_content[: start + len(INDEX_START_MARKER)] + "\n" + block + "\n" + index_content[end:]
    )


def main(argv: list[str] | None = None) -> int:
    """Render all generated files and report stale output in check mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if generated files are stale instead of writing them.",
    )
    args = parser.parse_args(argv)

    registry = build_default_registry()
    registrations = registry.all()
    if not registrations:
        print("No games registered.", file=sys.stderr)
        return 1

    stale: list[str] = []

    for registration in registrations:
        target = GAMES_DIR / f"{registration.identifier}.md"
        content = render_page(registration)
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current != content:
                stale.append(str(target))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"Generated: {target}")

    index_content = INDEX_FILE.read_text(encoding="utf-8")
    updated_index = sync_index(index_content, registrations)
    if args.check:
        if updated_index != index_content:
            stale.append(str(INDEX_FILE))
    else:
        INDEX_FILE.write_text(updated_index, encoding="utf-8")
        print(f"Generated: {INDEX_FILE} game list")

    if stale:
        for path in stale:
            print(f"Stale: {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
