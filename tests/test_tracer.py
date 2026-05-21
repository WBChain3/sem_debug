from __future__ import annotations

import os

from models import DEFAULT_THRESHOLD, Verdict
from tracer import trace


def test_drift_case():
    result, verdict = trace(
        "tests/fixtures/output_draft.md",
        ["tests/fixtures/input_source_alpha.md", "tests/fixtures/input_source_beta.md"],
    )
    assert result.stage == ""
    assert result.output_file == "tests/fixtures/output_draft.md"
    assert result.input_files == [
        "tests/fixtures/input_source_alpha.md",
        "tests/fixtures/input_source_beta.md",
    ]
    assert len(result.matches) >= 1
    assert len(result.unattributed) >= 1
    for m in result.matches:
        assert m.method == "tfidf"
        assert 0.0 <= m.score <= 1.0
    assert verdict.status == "DRIFT"
    assert verdict.exit_code == 1


def test_clean_case():
    result, verdict = trace(
        "tests/fixtures/output_clean.md",
        ["tests/fixtures/input_source_alpha.md", "tests/fixtures/input_source_beta.md"],
    )
    assert len(result.unattributed) == 0
    assert len(result.matches) >= 1
    assert verdict.status == "CLEAN"
    assert verdict.exit_code == 0


def test_stage_field_populated():
    result, verdict = trace(
        "tests/fixtures/output_draft.md",
        ["tests/fixtures/input_source_alpha.md", "tests/fixtures/input_source_beta.md"],
        stage="02_draft",
    )
    assert result.stage == "02_draft"


def test_unattributed_carries_best_score():
    result, verdict = trace(
        "tests/fixtures/output_draft.md",
        ["tests/fixtures/input_source_alpha.md", "tests/fixtures/input_source_beta.md"],
    )
    for passage, score in result.unattributed:
        assert isinstance(score, float)
        assert 0.0 <= score < DEFAULT_THRESHOLD


def test_empty_inputs():
    result, verdict = trace(
        "tests/fixtures/output_draft.md",
        [],
    )
    assert len(result.matches) == 0
    assert len(result.unattributed) > 0
    for passage, score in result.unattributed:
        assert score == 0.0
    assert verdict.status == "DRIFT"


def test_source_file_paths_preserved():
    input_rel = "tests/fixtures/input_source_alpha.md"
    result, verdict = trace(
        "tests/fixtures/output_draft.md",
        [input_rel],
    )
    norm_input = os.path.normpath(input_rel)
    for m in result.matches:
        assert m.input_passage.source_file.startswith(norm_input)
    assert result.input_files[0] == input_rel
