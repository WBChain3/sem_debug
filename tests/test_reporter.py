from __future__ import annotations

from sem_debug.models import Match, Passage, TraceResult, Verdict
from sem_debug.reporter import render

PASSAGE_OUT_1 = Passage(
    text="Models are increasingly deployed in quantized form.",
    source_file="tests/fixtures/output_draft.md",
    line_start=1,
    line_end=2,
)
PASSAGE_IN_1 = Passage(
    text="Post-training quantization reduces memory and latency.",
    source_file="tests/fixtures/input_source_alpha.md",
    line_start=3,
    line_end=4,
)
PASSAGE_OUT_2 = Passage(
    text="Orcas in the Pacific Northwest hunt in coordinated pods.",
    source_file="tests/fixtures/output_draft.md",
    line_start=5,
    line_end=6,
)
MATCH_1 = Match(
    output_passage=PASSAGE_OUT_1,
    input_passage=PASSAGE_IN_1,
    score=0.8421,
    method="tfidf",
)


def test_report_header_present():
    tr = TraceResult(
        stage="02_draft",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "# sem_debug Trace Report" in output


def test_stage_line_present():
    tr = TraceResult(
        stage="02_draft",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "Stage: 02_draft" in output


def test_stage_line_absent_when_empty():
    tr = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "Stage:" not in output


def test_output_line_present():
    tr = TraceResult(
        stage="02_draft",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "Output: tests/fixtures/output_draft.md" in output


def test_inputs_line_present():
    tr = TraceResult(
        stage="02_draft",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "Inputs:" in output
    assert "input_source_alpha.md" in output


def test_attributed_section_present():
    tr = TraceResult(
        stage="02_draft",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "## Attributed Passages" in output


def test_attributed_passage_text_quoted():
    tr = TraceResult(
        stage="02_draft",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    for line in PASSAGE_OUT_1.text.splitlines():
        assert f"> {line}" in output


def test_attributed_source_line():
    tr = TraceResult(
        stage="02_draft",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "Source: tests/fixtures/input_source_alpha.md (lines 3\u20134)" in output


def test_attributed_score_line():
    tr = TraceResult(
        stage="02_draft",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "Score: 0.8421 | Method: tfidf" in output


def test_unattributed_section_present():
    tr = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[],
        unattributed=[(PASSAGE_OUT_2, 0.0312)],
    )
    v = Verdict(status="DRIFT", exit_code=1)
    output = render(tr, v)
    assert "## Unattributed Passages" in output


def test_unattributed_passage_text_quoted():
    tr = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[],
        unattributed=[(PASSAGE_OUT_2, 0.0312)],
    )
    v = Verdict(status="DRIFT", exit_code=1)
    output = render(tr, v)
    for line in PASSAGE_OUT_2.text.splitlines():
        assert f"> {line}" in output


def test_unattributed_score_line():
    tr = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[],
        unattributed=[(PASSAGE_OUT_2, 0.0312)],
    )
    v = Verdict(status="DRIFT", exit_code=1)
    output = render(tr, v)
    assert "Best score: 0.0312 | No source in declared inputs." in output


def test_unattributed_section_absent_when_clean():
    tr = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "## Unattributed Passages" not in output


def test_attributed_section_absent_when_all_unattributed():
    tr = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[],
        unattributed=[(PASSAGE_OUT_2, 0.0312)],
    )
    v = Verdict(status="DRIFT", exit_code=1)
    output = render(tr, v)
    assert "## Attributed Passages" not in output


def test_verdict_block_present():
    tr = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[],
        unattributed=[(PASSAGE_OUT_2, 0.0312)],
    )
    v = Verdict(status="DRIFT", exit_code=1)
    output = render(tr, v)
    assert "## Verdict" in output


def test_verdict_status_drift():
    tr = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[],
        unattributed=[(PASSAGE_OUT_2, 0.0312)],
    )
    v = Verdict(status="DRIFT", exit_code=1)
    output = render(tr, v)
    assert "Status: DRIFT" in output


def test_verdict_status_clean():
    tr = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v = Verdict(status="CLEAN", exit_code=0)
    output = render(tr, v)
    assert "Status: CLEAN" in output


def test_verdict_exit_code():
    tr_drift = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[],
        unattributed=[(PASSAGE_OUT_2, 0.0312)],
    )
    v_drift = Verdict(status="DRIFT", exit_code=1)
    output_drift = render(tr_drift, v_drift)
    assert "Exit code: 1" in output_drift

    tr_clean = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v_clean = Verdict(status="CLEAN", exit_code=0)
    output_clean = render(tr_clean, v_clean)
    assert "Exit code: 0" in output_clean


def test_verdict_unattributed_count():
    tr_one = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[],
        unattributed=[(PASSAGE_OUT_2, 0.0312)],
    )
    v_one = Verdict(status="DRIFT", exit_code=1)
    output_one = render(tr_one, v_one)
    assert "Unattributed passages: 1" in output_one

    tr_zero = TraceResult(
        stage="",
        output_file="tests/fixtures/output_draft.md",
        input_files=["tests/fixtures/input_source_alpha.md"],
        matches=[MATCH_1],
        unattributed=[],
    )
    v_zero = Verdict(status="CLEAN", exit_code=0)
    output_zero = render(tr_zero, v_zero)
    assert "Unattributed passages: 0" in output_zero
