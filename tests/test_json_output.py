from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

from sem_debug.models import DEFAULT_THRESHOLD, Passage, Match, TraceResult, Verdict


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "sem_debug.cli", *args],
        capture_output=True,
        text=True,
    )


def _make_trace_result() -> TraceResult:
    """Build a common TraceResult fixture for unit tests."""
    ip = Passage(text="Input passage text", source_file="source.md", line_start=1, line_end=2)
    op = Passage(text="Output passage text", source_file="output.md", line_start=3, line_end=4)
    match = Match(output_passage=op, input_passage=ip, score=0.4821, method="tfidf")
    unat = Passage(text="Unattributed passage content here for testing", source_file="output.md", line_start=5, line_end=6)
    return TraceResult(
        stage="synthesis",
        output_file="output.md",
        input_files=["source.md"],
        matches=[match],
        unattributed=[(unat, 0.12)],
    )


class TestTraceResultToDict:
    def test_trace_result_to_dict_structure(self):
        result = _make_trace_result()
        verdict = Verdict(status="CLEAN", exit_code=0)
        d = result.to_dict(verdict, DEFAULT_THRESHOLD)
        expected_keys = {"status", "exit_code", "stage", "threshold", "attributed", "unattributed"}
        assert set(d.keys()) == expected_keys
        assert isinstance(d["status"], str)
        assert isinstance(d["exit_code"], int)
        assert isinstance(d["stage"], str)
        assert isinstance(d["threshold"], float)
        assert isinstance(d["attributed"], list)
        assert isinstance(d["unattributed"], list)

    def test_attributed_match_dict_keys(self):
        result = _make_trace_result()
        verdict = Verdict(status="CLEAN", exit_code=0)
        d = result.to_dict(verdict, DEFAULT_THRESHOLD)
        att = d["attributed"][0]
        expected_att_keys = {"passage_index", "source_file", "source_line_start", "score", "method"}
        assert set(att.keys()) == expected_att_keys
        assert att["method"] in ("tfidf", "semantic")
        assert isinstance(att["score"], float)
        assert isinstance(att["passage_index"], int)

    def test_unattributed_dict_keys(self):
        result = _make_trace_result()
        verdict = Verdict(status="CLEAN", exit_code=0)
        d = result.to_dict(verdict, DEFAULT_THRESHOLD)
        unat = d["unattributed"][0]
        expected_unat_keys = {"passage_index", "best_failed_score", "text_preview"}
        assert set(unat.keys()) == expected_unat_keys
        assert isinstance(unat["best_failed_score"], float)
        assert isinstance(unat["text_preview"], str)
        assert len(unat["text_preview"]) <= 80

    def test_verdict_dict_keys(self):
        verdict = Verdict(status="CLEAN", exit_code=0)
        d = verdict.to_dict()
        assert set(d.keys()) == {"status", "exit_code"}
        assert d["status"] == "CLEAN"
        assert d["exit_code"] == 0

    def test_verdict_to_dict(self):
        verdict = Verdict(status="CLEAN", exit_code=0)
        assert verdict.to_dict() == {"status": "CLEAN", "exit_code": 0}


class TestRenderJson:
    def test_render_json_returns_string(self):
        result = _make_trace_result()
        verdict = Verdict(status="CLEAN", exit_code=0)
        from sem_debug.reporter import render_json
        s = render_json(result, verdict, DEFAULT_THRESHOLD)
        parsed = json.loads(s)
        assert isinstance(parsed, dict)
        assert parsed["status"] == "CLEAN"


class TestCliFormatJson:
    def test_cli_format_json_exit_0(self):
        result = _run(
            "tests/fixtures/output_clean.md",
            "--inputs",
            "tests/fixtures/input_source_alpha.md",
            "--format", "json",
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed["status"] == "CLEAN"
        assert parsed["exit_code"] == 0

    def test_cli_format_json_exit_1(self):
        result = _run(
            "tests/fixtures/output_draft.md",
            "--inputs",
            "tests/fixtures/input_source_alpha.md",
            "--format", "json",
        )
        assert result.returncode == 1
        parsed = json.loads(result.stdout)
        assert parsed["status"] == "DRIFT"
        assert len(parsed["unattributed"]) > 0

    def test_cli_json_shorthand(self):
        result = _run(
            "tests/fixtures/output_clean.md",
            "--inputs",
            "tests/fixtures/input_source_alpha.md",
            "--json",
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed["status"] == "CLEAN"

    def test_cli_report_with_json(self):
        report_path = "tests/fixtures/tmp_report.json"
        try:
            result = _run(
                "tests/fixtures/output_clean.md",
                "--inputs",
                "tests/fixtures/input_source_alpha.md",
                "--format", "json",
                "--report", report_path,
            )
            assert result.returncode == 0
            assert result.stdout == ""
            assert os.path.exists(report_path)
            content = pathlib.Path(report_path).read_text()
            parsed = json.loads(content)
            assert isinstance(parsed, dict)
            assert parsed["status"] == "CLEAN"
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)