from __future__ import annotations

"""Frozen contract test: to_dict() schema must not drift.

If this test fails, the JSON contract has changed and research_loop's
Trace.check() may break. Do not change to_dict() shape without updating
this test and the help epilog.
"""

from sem_debug.models import DEFAULT_THRESHOLD, Passage, Match, TraceResult, Verdict


def test_trace_result_dict_keys():
    ip = Passage(text="input", source_file="src.md", line_start=1, line_end=2)
    op = Passage(text="output", source_file="out.md", line_start=3, line_end=4)
    match = Match(output_passage=op, input_passage=ip, score=0.5, method="tfidf")
    unat = Passage(text="unattributed content here", source_file="out.md", line_start=5, line_end=6)
    tr = TraceResult(
        stage="synthesis",
        output_file="out.md",
        input_files=["src.md"],
        matches=[match],
        unattributed=[(unat, 0.12)],
        output_passages=[op, unat],
    )
    d = tr.to_dict(Verdict(status="CLEAN", exit_code=0), DEFAULT_THRESHOLD)
    expected = {"status", "exit_code", "stage", "threshold", "attributed", "unattributed"}
    assert set(d.keys()) == expected


def test_attributed_match_dict_keys():
    ip = Passage(text="input", source_file="src.md", line_start=1, line_end=2)
    op = Passage(text="output", source_file="out.md", line_start=3, line_end=4)
    match = Match(output_passage=op, input_passage=ip, score=0.5, method="tfidf")
    tr = TraceResult(
        stage="synthesis",
        output_file="out.md",
        input_files=["src.md"],
        matches=[match],
        unattributed=[],
        output_passages=[op],
    )
    d = tr.to_dict(Verdict(status="CLEAN", exit_code=0), DEFAULT_THRESHOLD)
    att = d["attributed"][0]
    assert set(att.keys()) == {"passage_index", "source_file", "source_line_start", "score", "method"}
    assert att["method"] in ("tfidf", "semantic")
    assert isinstance(att["score"], float)


def test_unattributed_dict_keys():
    op = Passage(text="output", source_file="out.md", line_start=3, line_end=4)
    unat = Passage(text="unattributed content here for testing purposes", source_file="out.md", line_start=5, line_end=6)
    tr = TraceResult(
        stage="synthesis",
        output_file="out.md",
        input_files=["src.md"],
        matches=[],
        unattributed=[(unat, 0.12)],
        output_passages=[op, unat],
    )
    d = tr.to_dict(Verdict(status="DRIFT", exit_code=1), DEFAULT_THRESHOLD)
    unatt = d["unattributed"][0]
    assert set(unatt.keys()) == {"passage_index", "best_failed_score", "text_preview"}
    assert isinstance(unatt["best_failed_score"], float)
    assert isinstance(unatt["text_preview"], str)
    assert len(unatt["text_preview"]) <= 80


def test_verdict_dict_keys():
    verdict = Verdict(status="CLEAN", exit_code=0)
    d = verdict.to_dict()
    assert set(d.keys()) == {"status", "exit_code"}


def test_method_semantic_preserved():
    ip = Passage(text="input", source_file="src.md", line_start=1, line_end=2)
    op = Passage(text="output", source_file="out.md", line_start=3, line_end=4)
    match = Match(output_passage=op, input_passage=ip, score=0.6, method="semantic")
    tr = TraceResult(
        stage="synthesis",
        output_file="out.md",
        input_files=["src.md"],
        matches=[match],
        unattributed=[],
        output_passages=[op],
    )
    d = tr.to_dict(Verdict(status="CLEAN", exit_code=0), DEFAULT_THRESHOLD)
    assert d["attributed"][0]["method"] == "semantic"