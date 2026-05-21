from __future__ import annotations

from matcher import match_passages
from models import DEFAULT_THRESHOLD
from parser import parse_file


def test_zone1_high_overlap_above_threshold():
    input_passages = parse_file("tests/fixtures/input_source_alpha.md")
    output_passages = parse_file("tests/fixtures/output_draft.md")
    # Zone 1 is the first output passage (line 2 — high lexical overlap with alpha)
    zone1 = output_passages[0]
    matched, unattributed = match_passages([zone1], input_passages)
    assert len(matched) == 1
    assert matched[0].score >= DEFAULT_THRESHOLD
    assert matched[0].method == "tfidf"
    # Should match the first paragraph of alpha (same vocabulary)
    assert "input_source_alpha.md" in matched[0].input_passage.source_file


def test_zone2_paraphrase_below_threshold():
    input_passages = parse_file("tests/fixtures/input_source_beta.md")
    output_passages = parse_file("tests/fixtures/output_draft.md")
    # Zone 2 is the second output passage (line 5 — paraphrase of beta)
    zone2 = output_passages[1]
    matched, unattributed = match_passages([zone2], input_passages)
    assert len(matched) == 0
    assert len(unattributed) == 1
    assert unattributed[0][0] == zone2
    assert unattributed[0][1] < DEFAULT_THRESHOLD


def test_zone3_unrelated_returns_none():
    input_passages_alpha = parse_file("tests/fixtures/input_source_alpha.md")
    input_passages_beta = parse_file("tests/fixtures/input_source_beta.md")
    all_inputs = input_passages_alpha + input_passages_beta
    output_passages = parse_file("tests/fixtures/output_draft.md")
    # Zone 3 is the third output passage (line 8 — Tour de France, unrelated)
    zone3 = output_passages[2]
    matched, unattributed = match_passages([zone3], all_inputs)
    assert len(matched) == 0
