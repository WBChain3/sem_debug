from __future__ import annotations

import pathlib
import sys

from .models import Passage


def parse_file(path: str) -> list[Passage]:
    """Parse a markdown file into passages. Delegates to parse_file_sections with no section filter."""
    return parse_file_sections(path, sections=None)


def parse_file_sections(path: str, sections: list[str] | None = None) -> list[Passage]:
    """Parse a markdown file, optionally extracting only named H2 sections.

    If sections is None, behaves exactly like parse_file() — returns all passages.
    If sections is provided, only passages inside the named H2 sections are returned.
    A passage belongs to a section if it appears after the section's H2 header
    and before the next H2 header or EOF.

    Headers (H1-H6) merge with following paragraphs per AD-05. This rule applies
    within sections exactly as it does globally.
    """
    filepath = pathlib.Path(path)
    if filepath.stat().st_size == 0:
        return []

    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Identify fenced code block ranges (0-based line indices)
    code_block_ranges: list[tuple[int, int]] = []
    in_code_block = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            if not in_code_block:
                code_block_ranges.append((i, i))
                in_code_block = True
            else:
                code_block_ranges[-1] = (code_block_ranges[-1][0], i)
                in_code_block = False

    # Identify HTML comment ranges (0-based line indices)
    comment_ranges: list[tuple[int, int]] = []
    in_comment = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_comment and stripped.startswith("<!--"):
            if "-->" in stripped:
                comment_ranges.append((i, i))
            else:
                in_comment = True
                comment_ranges.append((i, i))
        elif in_comment:
            if "-->" in stripped:
                comment_ranges[-1] = (comment_ranges[-1][0], i)
                in_comment = False
            else:
                comment_ranges[-1] = (comment_ranges[-1][0], i)

    def _skipped(idx: int) -> bool:
        for start, end in code_block_ranges:
            if start <= idx <= end:
                return True
        for start, end in comment_ranges:
            if start <= idx <= end:
                return True
        return False

    # Determine which H2 sections to include
    # Map H2 header line index -> section name. Track section boundaries.
    section_ranges: list[tuple[int, int, str]] = []
    current_h2_line: int | None = None
    current_section_name: str | None = None
    for i, line in enumerate(lines):
        if _skipped(i):
            continue
        stripped = line.strip()
        if stripped.startswith("## ") and not stripped.startswith("###"):
            h2_name = stripped[3:].strip()
            if current_h2_line is not None:
                section_ranges.append((current_h2_line, i - 1, current_section_name))
            current_h2_line = i
            current_section_name = h2_name
    if current_h2_line is not None:
        section_ranges.append((current_h2_line, len(lines) - 1, current_section_name))

    def _in_requested_section(line_idx: int) -> bool:
        """Return True if line_idx falls within any requested section.

        O(n×m) where n=blocks, m=section_ranges. Acceptable for ICM workspace
        sizes (typically <10 sections, <50 passages).
        """
        if sections is None:
            return True
        for _start, _end, sec_name in section_ranges:
            if _start <= line_idx <= _end and sec_name in sections:
                return True
        return False

    # Warn about requested sections not found in the file
    if sections is not None:
        found_sections = {sec_name for _, _, sec_name in section_ranges}
        for s in sections:
            if s not in found_sections:
                print(f"Warning: section '{s}' not found in {path}", file=sys.stderr)

    # Group non-code, non-blank lines into blocks
    blocks: list[tuple[int, int, list[str]]] = []
    cur_lines: list[str] = []
    cur_start: int | None = None

    for i, line in enumerate(lines):
        if _skipped(i):
            if cur_lines:
                blocks.append((cur_start, i - 1, cur_lines))
                cur_lines = []
                cur_start = None
            continue

        if line.strip() == "":
            if cur_lines:
                blocks.append((cur_start, i - 1, cur_lines))
                cur_lines = []
                cur_start = None
        else:
            if cur_start is None:
                cur_start = i
            cur_lines.append(line)

    if cur_lines:
        blocks.append((cur_start, len(lines) - 1, cur_lines))

    # Merge header blocks with following prose blocks;
    # standalone headers (no prose to merge) are dropped.
    merged: list[tuple[int, int, str]] = []
    i = 0
    while i < len(blocks):
        start, end, text_lines = blocks[i]
        first = text_lines[0].strip() if text_lines else ""

        if first.startswith("#") and i + 1 < len(blocks):
            next_start, next_end, next_lines = blocks[i + 1]
            next_first = next_lines[0].strip() if next_lines else ""
            # Only merge if the next block is prose (not another header)
            if not next_first.startswith("#"):
                merged_text = "\n".join(text_lines + [""] + next_lines)
                merged.append((start, next_end, merged_text))
                i += 2
                continue

        # Standalone header — drop; otherwise keep as passage
        if not first.startswith("#"):
            merged.append((start, end, "\n".join(text_lines)))
        i += 1

    source_file = str(filepath)
    passages: list[Passage] = []
    for start_0, end_0, text in merged:
        if not text.strip():
            continue
        # Filter by section membership
        if not _in_requested_section(start_0):
            continue
        passages.append(
            Passage(
                text=text,
                source_file=source_file,
                line_start=start_0 + 1,
                line_end=end_0 + 1,
            )
        )

    return passages
