from __future__ import annotations

from pathlib import Path

from sem_debug.tracer import trace


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_trace_with_context_md(tmp_path: Path):
    """CONTEXT.md with Inputs table pointing to existing input via absolute path."""
    alpha = FIXTURES / "input_source_alpha.md"
    beta = FIXTURES / "input_source_beta.md"
    output = str(FIXTURES / "output_clean.md")

    # CONTEXT.md with absolute paths (no section)
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text(
        f"## Inputs\n\n| Source |\n|--------|\n| {alpha} |\n| {beta} |\n",
        encoding="utf-8",
    )

    result_with_ctx, verdict_with_ctx = trace(
        output_file=output,
        input_files=[str(alpha), str(beta)],
        context_md=ctx,
    )
    result_no_ctx, verdict_no_ctx = trace(
        output_file=output,
        input_files=[str(alpha), str(beta)],
    )
    assert verdict_with_ctx.status == verdict_no_ctx.status
    assert verdict_with_ctx.exit_code == verdict_no_ctx.exit_code


def test_trace_context_md_falls_back(tmp_path: Path):
    """CONTEXT.md with no Inputs table falls back to whole-file input_paths."""
    alpha = FIXTURES / "input_source_alpha.md"
    beta = FIXTURES / "input_source_beta.md"
    output = str(FIXTURES / "output_clean.md")

    # CONTEXT.md with no Inputs table
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text("---\nquestion: test\n---\n\n## Background\n\nNo inputs table.\n", encoding="utf-8")

    result_with_ctx, verdict_with_ctx = trace(
        output_file=output,
        input_files=[str(alpha), str(beta)],
        context_md=ctx,
    )
    result_no_ctx, verdict_no_ctx = trace(
        output_file=output,
        input_files=[str(alpha), str(beta)],
    )
    assert verdict_with_ctx.status == verdict_no_ctx.status
    assert verdict_with_ctx.exit_code == verdict_no_ctx.exit_code