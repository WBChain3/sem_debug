from __future__ import annotations

from .models import TraceResult, Verdict


def render(trace_result: TraceResult, verdict: Verdict) -> str:
    parts: list[str] = []

    # Header block
    parts.append("# sem_debug Trace Report")
    parts.append("")
    if trace_result.stage:
        parts.append(f"Stage: {trace_result.stage}")
    parts.append(f"Output: {trace_result.output_file}")
    inputs_line = ", ".join(trace_result.input_files)
    parts.append(f"Inputs: {inputs_line}")

    parts.append("")
    parts.append("---")
    parts.append("")

    # Attributed section
    if trace_result.matches:
        parts.append("## Attributed Passages")
        parts.append("")
        for i, m in enumerate(trace_result.matches):
            op = m.output_passage
            en_dash = "\u2013"
            parts.append(f"### Passage (lines {op.line_start}{en_dash}{op.line_end})")
            for line in op.text.splitlines():
                parts.append(f"> {line}")
            parts.append("")
            ip = m.input_passage
            parts.append(
                f"Source: {ip.source_file} (lines {ip.line_start}{en_dash}{ip.line_end})"
            )
            parts.append(f"Score: {m.score:.4f} | Method: {m.method}")
            if i < len(trace_result.matches) - 1:
                parts.append("")
                parts.append("---")
            parts.append("")
        parts.append("---")
        parts.append("")

    # Unattributed section
    if trace_result.unattributed:
        parts.append("## Unattributed Passages")
        parts.append("")
        unattributed_list = trace_result.unattributed
        for i, (passage, best_score) in enumerate(unattributed_list):
            en_dash = "\u2013"
            parts.append(
                f"### Passage (lines {passage.line_start}{en_dash}{passage.line_end})"
            )
            for line in passage.text.splitlines():
                parts.append(f"> {line}")
            parts.append("")
            parts.append(
                f"Best score: {best_score:.4f} | No source in declared inputs."
            )
            if i < len(unattributed_list) - 1:
                parts.append("")
                parts.append("---")
            parts.append("")
        parts.append("---")
        parts.append("")

    # Verdict block (always present)
    parts.append("## Verdict")
    parts.append("")
    parts.append(f"Status: {verdict.status}")
    parts.append(f"Unattributed passages: {len(trace_result.unattributed)}")
    parts.append(f"Exit code: {verdict.exit_code}")

    return "\n".join(parts)
