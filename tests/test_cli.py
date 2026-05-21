from __future__ import annotations

import os
import sys
import subprocess
import pathlib

import pytest


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "sem_debug.py", *args],
        capture_output=True,
        text=True,
    )


class TestCliClean:
    def test_cli_clean_exit_0(self):
        result = _run(
            "tests/fixtures/output_clean.md",
            "--inputs",
            "tests/fixtures/input_source_alpha.md",
            "tests/fixtures/input_source_beta.md",
        )
        assert result.returncode == 0
        assert "Status: CLEAN" in result.stdout
        assert "Verdict" in result.stdout


class TestCliDrift:
    def test_cli_drift_exit_1(self):
        result = _run(
            "tests/fixtures/output_draft.md",
            "--inputs",
            "tests/fixtures/input_source_alpha.md",
            "tests/fixtures/input_source_beta.md",
        )
        assert result.returncode == 1
        assert "Status: DRIFT" in result.stdout


class TestCliStrict:
    def test_cli_strict_blocked_exit_2(self):
        result = _run(
            "tests/fixtures/output_draft.md",
            "--inputs",
            "tests/fixtures/input_source_alpha.md",
            "tests/fixtures/input_source_beta.md",
            "--strict",
        )
        assert result.returncode == 2
        assert "Status: BLOCKED" in result.stdout


class TestCliReport:
    def test_cli_report_writes_to_file(self):
        report_path = "tests/fixtures/tmp_report.md"
        try:
            result = _run(
                "tests/fixtures/output_clean.md",
                "--inputs",
                "tests/fixtures/input_source_alpha.md",
                "tests/fixtures/input_source_beta.md",
                "--report",
                report_path,
            )
            assert os.path.exists(report_path)
            content = pathlib.Path(report_path).read_text()
            assert "Status: CLEAN" in content
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)


class TestCliStage:
    def test_cli_stage_flag(self):
        result = _run(
            "tests/fixtures/output_draft.md",
            "--inputs",
            "tests/fixtures/input_source_alpha.md",
            "tests/fixtures/input_source_beta.md",
            "--stage",
            "02_draft",
        )
        assert "Stage: 02_draft" in result.stdout


class TestCliThreshold:
    def test_cli_threshold_flag(self):
        result = _run(
            "tests/fixtures/output_draft.md",
            "--inputs",
            "tests/fixtures/input_source_alpha.md",
            "tests/fixtures/input_source_beta.md",
            "--threshold",
            "0.9",
        )
        assert result.returncode == 1
        assert "Unattributed passages: 2" in result.stdout


class TestCliSemantic:
    def test_cli_semantic_flag_imports(self):
        result = _run(
            "tests/fixtures/output_draft.md",
            "--inputs",
            "tests/fixtures/input_source_alpha.md",
            "tests/fixtures/input_source_beta.md",
            "--semantic",
        )
        # If sentence-transformers is not installed, expect graceful error
        if "sentence-transformers is required" in result.stderr:
            assert result.returncode != 0
        else:
            # If installed, must not crash
            assert result.returncode in (0, 1)


class TestCliNoInputs:
    def test_cli_no_inputs_error(self):
        result = _run("tests/fixtures/output_draft.md")
        assert result.returncode == 1
        assert "error" in result.stderr
