from __future__ import annotations

from pathlib import Path

from .models import DEFAULT_THRESHOLD, Passage, TraceResult, Verdict
from .matcher import match_passages
from .parser import parse_file, parse_file_sections
from .workspace_parser import read_context_md


def trace(
    output_file: str,
    input_files: list[str],
    stage: str = "",
    threshold: float = DEFAULT_THRESHOLD,
    semantic: bool = False,
    context_md: Path | None = None,
) -> tuple[TraceResult, Verdict]:
    """Trace attribution of output passages against input sources.

    Parameters:
      output_file: path to the markdown file whose passages are to be checked
      input_files: list of markdown source files (used when context_md is None or has no Inputs table)
      stage: label for the trace report
      threshold: similarity threshold (default 0.35)
      semantic: enable sentence-transformers fallback on TF-IDF failures
      context_md: Path to an ICM-style CONTEXT.md file, or None for whole-file input loading.
                  When provided, only the sources and sections declared in its Inputs table are read.
    """
    output_passages = parse_file(output_file)
    input_passages: list[Passage] = []  # retained: Passage used in type annotation; removing breaks mypy

    if context_md is not None:
        # CONTEXT.md path resolution: resolve relative to context_md.parent (the stage directory),
        # not output_file.parent. CONTEXT.md lives in the workspace root / stage dir,
        # while output_file may be in a fixtures/ subdirectory.
        decls = read_context_md(context_md)
        if decls:
            base_dir = context_md.parent
            for decl in decls:
                resolved = (base_dir / decl.source).resolve()
                if decl.section:
                    input_passages.extend(parse_file_sections(str(resolved), [decl.section]))
                else:
                    input_passages.extend(parse_file(str(resolved)))
        else:
            # No Inputs table found — fall back to whole-file reading of input_paths
            for path in input_files:
                input_passages.extend(parse_file(path))
    else:
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
        output_passages=output_passages,
    )

    if len(unattributed) == 0:
        verdict = Verdict(status="CLEAN", exit_code=0)
    else:
        verdict = Verdict(status="DRIFT", exit_code=1)

    return trace_result, verdict
