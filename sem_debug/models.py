from __future__ import annotations

from dataclasses import dataclass


DEFAULT_THRESHOLD = 0.35


@dataclass
class Passage:
    text: str
    source_file: str
    line_start: int
    line_end: int


@dataclass
class Match:
    output_passage: Passage
    input_passage: Passage
    score: float
    method: str


@dataclass
class TraceResult:
    stage: str
    output_file: str
    input_files: list[str]
    matches: list[Match]
    unattributed: list[tuple[Passage, float]]


@dataclass
class Verdict:
    status: str
    exit_code: int
