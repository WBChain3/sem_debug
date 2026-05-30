from __future__ import annotations

from sem_debug.models import DEFAULT_THRESHOLD


def test_default_threshold():
    assert DEFAULT_THRESHOLD == 0.35
