from __future__ import annotations

import pathlib

from models import Passage


def parse_file(path: str) -> list[Passage]:
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
        passages.append(
            Passage(
                text=text,
                source_file=source_file,
                line_start=start_0 + 1,
                line_end=end_0 + 1,
            )
        )

    return passages
