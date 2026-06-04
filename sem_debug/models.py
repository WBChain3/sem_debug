from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
    output_passages: list[Passage] | None = None

    def to_dict(self, verdict: Verdict, threshold: float = DEFAULT_THRESHOLD) -> dict[str, object]:
        """Return a flat dict representation for JSON serialization.

        Keys: status, exit_code, stage, threshold,
              attributed (list of dicts), unattributed (list of dicts).
        Each match dict contains: passage_index, source_file, source_line_start,
        score, method ("tfidf" | "semantic").
        passage_index is the original index of the passage in the output file.
        """
        # Map Passage object identity to its original index in the output.
        # identity check (is) is safe here because match_passages returns the
        # same Passage instances that tracer.py put in output_passages.
        passage_to_index: dict[int, int] = {}
        if self.output_passages is not None:
            for i, p in enumerate(self.output_passages):
                passage_to_index[id(p)] = i

        attributed: list[dict[str, object]] = []
        for m in self.matches:
            op = m.output_passage
            idx = passage_to_index.get(id(op), -1)
            attributed.append({
                "passage_index": idx,
                "source_file": m.input_passage.source_file,
                "source_line_start": m.input_passage.line_start,
                "score": round(m.score, 4),
                "method": m.method,
            })

        unattributed: list[dict[str, object]] = []
        for passage, best_score in self.unattributed:
            idx = passage_to_index.get(id(passage), -1)
            unattributed.append({
                "passage_index": idx,
                "best_failed_score": round(best_score, 4),
                "text_preview": passage.text[:80],
            })

        return {
            "status": verdict.status,
            "exit_code": verdict.exit_code,
            "stage": self.stage,
            "threshold": threshold,
            "attributed": attributed,
            "unattributed": unattributed,
        }


@dataclass
class Verdict:
    status: str
    exit_code: int

    def to_dict(self) -> dict:
        """Return flat dict: {"status": self.status, "exit_code": self.exit_code}."""
        return {"status": self.status, "exit_code": self.exit_code}
