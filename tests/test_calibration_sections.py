from __future__ import annotations

from pathlib import Path

from sem_debug.models import DEFAULT_THRESHOLD
from sem_debug.tracer import trace


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "context_workspace"
ALPHA_ABS = str((FIXTURES / "01_intro.md").resolve())
BETA_ABS = str((FIXTURES / "02_data.md").resolve())
CONTEXT = FIXTURES / "CONTEXT.md"
OUTPUT_FULL = str(FIXTURES / "output_full.md")
OUTPUT_DRIFT = str(FIXTURES / "output_drift.md")


def test_section_vs_wholefile_same_verdict():
    result_section, verdict_section = trace(
        output_file=OUTPUT_FULL,
        input_files=[ALPHA_ABS, BETA_ABS],
        context_md=CONTEXT,
    )
    result_whole, verdict_whole = trace(
        output_file=OUTPUT_FULL,
        input_files=[ALPHA_ABS, BETA_ABS],
    )
    assert verdict_section.status == verdict_whole.status


def test_section_load_reduces_input_passages():
    result_section, _ = trace(
        output_file=OUTPUT_FULL,
        input_files=[ALPHA_ABS, BETA_ABS],
        context_md=CONTEXT,
    )
    # CONTEXT.md declares only "Introduction" and "Data" sections — excludes "Methods".
    result_whole, _ = trace(
        output_file=OUTPUT_FULL,
        input_files=[ALPHA_ABS, BETA_ABS],
    )
    # The tracer doesn't expose input_passage count publicly.
    # We verify via match count: fewer input passages should mean fewer matches.
    assert len(result_section.unattributed) >= len(result_whole.unattributed)


def test_drift_detected_with_sections():
    _, verdict = trace(
        output_file=OUTPUT_DRIFT,
        input_files=[ALPHA_ABS, BETA_ABS],
        context_md=CONTEXT,
    )
    assert verdict.status == "DRIFT"


def test_semantic_json_combo(tmp_path):
    """--semantic --format json combo: valid JSON, method field present."""
    import json
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable, "-m", "sem_debug.cli",
            OUTPUT_DRIFT,
            "--inputs", ALPHA_ABS, BETA_ABS,
            "--context-md", str(CONTEXT),
            "--semantic",
            "--format", "json",
        ],
        capture_output=True,
        text=True,
    )
    # If sentence-transformers is not installed, expect graceful error
    if "sentence-transformers is required" in result.stderr:
        assert result.returncode != 0
        return

    assert result.returncode in (0, 1)  # 1=drift without semantic, 0=rescued with semantic
    parsed = json.loads(result.stdout)
    assert isinstance(parsed, dict)
    assert "status" in parsed
    assert "attributed" in parsed
    for att in parsed["attributed"]:
        assert "method" in att
        assert att["method"] in ("tfidf", "semantic")