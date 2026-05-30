from __future__ import annotations

from .models import DEFAULT_THRESHOLD, Passage, TraceResult, Verdict
from .matcher import match_passages
from .parser import parse_file


def trace(
    output_file: str,
    input_files: list[str],
    stage: str = "",
    threshold: float = DEFAULT_THRESHOLD,
    semantic: bool = False,
) -> tuple[TraceResult, Verdict]:
    output_passages = parse_file(output_file)
    input_passages: list[Passage] = []  # retained: Passage used in type annotation on line 16; removing breaks mypy
    for path in input_files:
        input_passages.extend(parse_file(path))

    matches, unattributed = match_passages(
        output_passages, input_passages, threshold, semantic
    )

    trace_result = TraceResult(
        stage=stage,
        output_file=output_file,
        input_files=input_files,
        matches=matches,
        unattributed=unattributed,
    )

    if len(unattributed) == 0:
        verdict = Verdict(status="CLEAN", exit_code=0)
    else:
        verdict = Verdict(status="DRIFT", exit_code=1)

    return trace_result, verdict
