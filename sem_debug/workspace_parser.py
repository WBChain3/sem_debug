from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

__all__ = ["InputDecl", "read_context_md"]


class InputDecl(NamedTuple):
    """A single declared input source with optional section name."""

    source: str
    section: str | None


def read_context_md(path: Path) -> list[InputDecl]:
    """Parse CONTEXT.md frontmatter and Inputs table.

    Returns a list of InputDecl tuples. Empty list if no Inputs table found.
    Never raises — malformed files return empty list with a warning printed
    to stderr (not logged; stderr is visible to CLI callers).
    """
    if not path.exists() or path.stat().st_size == 0:
        print(f"Warning: no Inputs table in {path}", file=sys.stderr)
        return []

    text = path.read_text(encoding="utf-8")

    # Skip YAML frontmatter (delimited by --- lines)
    frontmatter_match = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    if frontmatter_match:
        text = text[frontmatter_match.end():]

    # Find ## Inputs header (case-insensitive on "Inputs")
    inputs_match = re.search(r"^##\s+Inputs\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not inputs_match:
        print(f"Warning: no Inputs table in {path}", file=sys.stderr)
        return []

    # Extract content from after ## Inputs to next H2 or EOF
    table_start = inputs_match.end()
    remaining = text[table_start:].lstrip()
    next_h2 = re.search(r"^##\s", remaining, re.MULTILINE)
    if next_h2:
        table_text = remaining[:next_h2.start()].strip()
    else:
        table_text = remaining.strip()

    if not table_text:
        print(f"Warning: no Inputs table in {path}", file=sys.stderr)
        return []

    # Split on newlines, find the first markdown table
    lines = table_text.splitlines()
    table_lines: list[str] = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            in_table = True
            table_lines.append(stripped)
        elif in_table:
            # Table ended
            break

    if len(table_lines) < 2:
        print(f"Warning: no Inputs table in {path}", file=sys.stderr)
        return []

    # Skip header row and separator row
    data_rows = [line for line in table_lines if not line.startswith("|---")]
    if len(data_rows) < 2:
        print(f"Warning: no Inputs table in {path}", file=sys.stderr)
        return []

    data_rows = data_rows[1:]  # skip header

    results: list[InputDecl] = []
    for row in data_rows:
        cells = [cell.strip() for cell in row.split("|")[1:-1]]
        if not cells:
            continue
        source = cells[0]
        section = cells[1] if len(cells) > 1 and cells[1] else None
        if source:
            results.append(InputDecl(source=source, section=section))

    return results