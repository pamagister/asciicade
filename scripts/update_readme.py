# scripts/update_readme.py
from pathlib import Path

src = Path("docs/index.md")
dst = Path("README.md")

# Optional: prepend a note that it's generated
prefix = "<!-- This README.md is auto-generated from docs/index.md -->\n\n"

# Lese die Quelldatei explizit mit UTF-8 Kodierung
source_content = src.read_text(encoding="utf-8")

print(f"Generated: {dst} updated from {src}")
