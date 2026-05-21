from __future__ import annotations

from matcher import match_passages
from models import Match, Passage


def _passage(text: str) -> Passage:
    return Passage(text=text, source_file="test.md", line_start=1, line_end=1)


class TestEmptyInput:
    def test_empty_input_passages(self):
        output = [_passage("some text")]
        matched, unattributed = match_passages(output, [])
        assert len(matched) == 0
        assert len(unattributed) == len(output)

    def test_empty_output_passages(self):
        matched, unattributed = match_passages([], [_passage("input text")])
        assert len(matched) == 0
        assert len(unattributed) == 0

    def test_both_empty(self):
        matched, unattributed = match_passages([], [])
        assert len(matched) == 0
        assert len(unattributed) == 0


class TestCoreMatching:
    def test_one_value_per_output(self):
        outputs = [_passage("a"), _passage("b"), _passage("c")]
        inputs = [_passage("a")]
        matched, unattributed = match_passages(outputs, inputs)
        assert len(matched) + len(unattributed) == len(outputs)

    def test_best_match_selected(self):
        inputs = [
            _passage("Quantum physics describes subatomic particles."),
            _passage("The stock market declined sharply yesterday."),
        ]
        output = [_passage("Subatomic particles are governed by quantum physics.")]
        matched, unattributed = match_passages(output, inputs)
        assert len(matched) == 1
        assert matched[0].input_passage == inputs[0]

    def test_below_threshold_returns_none(self):
        inputs = [_passage("astrophysics black holes cosmology")]
        output = [_passage("chocolate chip cookie recipe baking")]
        matched, unattributed = match_passages(output, inputs)
        assert len(matched) == 0


class TestMatchProperties:
    def test_method_is_tfidf(self):
        inputs = [_passage("machine learning")]
        output = [_passage("machine learning is a field of AI")]
        matched, unattributed = match_passages(output, inputs)
        assert len(matched) == 1
        assert matched[0].method == "tfidf"

    def test_score_in_valid_range(self):
        inputs = [_passage("one two three four five")]
        output = [_passage("one two three")]
        matched, unattributed = match_passages(output, inputs)
        assert len(matched) == 1
        assert 0.0 <= matched[0].score <= 1.0


class TestEdgeCases:
    def test_empty_vocabulary_safe(self):
        inputs = [_passage("   ")]
        output = [_passage("   ")]
        matched, unattributed = match_passages(output, inputs)
        assert len(matched) == 0
        assert len(unattributed) == 1
