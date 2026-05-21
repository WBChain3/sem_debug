from __future__ import annotations

from models import DEFAULT_THRESHOLD


def test_default_threshold():
    assert DEFAULT_THRESHOLD == 0.35
