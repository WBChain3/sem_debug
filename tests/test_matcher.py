from __future__ import annotations

import pytest

from matcher import match_passages
from models import Match, Passage


def _passage(text: str) -> Passage:
    return Passage(text=text, source_file="test.md", line_start=1, line_end=1)


class TestEmptyInput:
    def test_empty_input_passages(self):
        output = [_passage("some text")]
        result = match_passages(output, [])
        assert result == [None]
        assert len(result) == len(output)

    def test_empty_output_passages(self):
        result = match_passages([], [_passage("input text")])
        assert result == []

    def test_both_empty(self):
        result = match_passages([], [])
        assert result == []


class TestCoreMatching:
    def test_one_value_per_output(self):
        outputs = [_passage("a"), _passage("b"), _passage("c")]
        inputs = [_passage("a")]
        result = match_passages(outputs, inputs)
        assert len(result) == len(outputs)

    def test_best_match_selected(self):
        inputs = [
            _passage("Quantum physics describes subatomic particles."),
            _passage("The stock market declined sharply yesterday."),
        ]
        output = [_passage("Subatomic particles are governed by quantum physics.")]
        result = match_passages(output, inputs)
        assert result[0] is not None
        assert result[0].input_passage == inputs[0]

    def test_below_threshold_returns_none(self):
        inputs = [_passage("astrophysics black holes cosmology")]
        output = [_passage("chocolate chip cookie recipe baking")]
        result = match_passages(output, inputs)
        assert result[0] is None


class TestMatchProperties:
    def test_method_is_tfidf(self):
        inputs = [_passage("machine learning")]
        output = [_passage("machine learning is a field of AI")]
        result = match_passages(output, inputs)
        assert result[0] is not None
        assert result[0].method == "tfidf"

    def test_score_in_valid_range(self):
        inputs = [_passage("one two three four five")]
        output = [_passage("one two three")]
        result = match_passages(output, inputs)
        assert result[0] is not None
        assert 0.0 <= result[0].score <= 1.0


class TestEdgeCases:
    def test_empty_vocabulary_safe(self):
        inputs = [_passage("   ")]
        output = [_passage("   ")]
        result = match_passages(output, inputs)
        assert result == [None]
        assert len(result) == 1
