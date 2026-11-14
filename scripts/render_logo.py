"""Render the PNG logo and favicon from their SVG sources."""

from __future__ import annotations

from pathlib import Path

import cairosvg

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "docs" / "_static" / "img"
TARGETS = (
    ("logo.svg", "logo.png", 512),
    ("favicon.svg", "favicon.png", 192),
)


def render_svg(source: Path, target: Path, size: int) -> None:
    """Render one square SVG to a PNG."""
    cairosvg.svg2png(
        url=str(source),
        write_to=str(target),
        output_width=size,
        output_height=size,
    )
    print(f"Generated: {target.relative_to(ROOT)} ({size}x{size})")


def main() -> None:
    """Render every configured SVG source."""
    for svg_name, png_name, size in TARGETS:
        source = IMAGE_DIR / svg_name
        if not source.is_file():
            raise FileNotFoundError(f"Missing SVG source: {source}")
        render_svg(source, IMAGE_DIR / png_name, size)


if __name__ == "__main__":
    main()
