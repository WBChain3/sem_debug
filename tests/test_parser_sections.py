from __future__ import annotations

from pathlib import Path

from sem_debug.parser import parse_file, parse_file_sections


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_file_sections_none(tmp_path: Path):
    content = """## Introduction

First paragraph.

## Methods

Second paragraph.
"""
    path = _write(tmp_path / "test.md", content)
    all_passages = parse_file(str(path))
    section_passages = parse_file_sections(str(path), sections=None)
    assert len(section_passages) == len(all_passages)


def test_parse_single_section(tmp_path: Path):
    content = """## Introduction

First paragraph.

## Methods

Second paragraph.
"""
    path = _write(tmp_path / "test.md", content)
    passages = parse_file_sections(str(path), sections=["Introduction"])
    assert len(passages) == 1
    assert "First paragraph" in passages[0].text


def test_parse_multiple_sections(tmp_path: Path):
    content = """## Introduction

First paragraph.

## Methods

Second paragraph.

## Results

Third paragraph.
"""
    path = _write(tmp_path / "test.md", content)
    passages = parse_file_sections(str(path), sections=["Introduction", "Results"])
    assert len(passages) == 2
    texts = [p.text for p in passages]
    assert any("First paragraph" in t for t in texts)
    assert any("Third paragraph" in t for t in texts)


def test_parse_missing_section(tmp_path: Path):
    content = """## Introduction

First paragraph.
"""
    path = _write(tmp_path / "test.md", content)
    passages = parse_file_sections(str(path), sections=["Nonexistent"])
    assert len(passages) == 0


def test_section_with_code_block_skipped(tmp_path: Path):
    content = """## Introduction

First paragraph.

```python
# This is code
x = 1
```

Second paragraph.

## Methods

Third paragraph.
"""
    path = _write(tmp_path / "test.md", content)
    passages = parse_file_sections(str(path), sections=["Introduction"])
    assert len(passages) == 2
    texts = [p.text for p in passages]
    assert any("First paragraph" in t for t in texts)
    assert any("Second paragraph" in t for t in texts)
    assert not any("x = 1" in t for t in texts)


def test_section_header_merge(tmp_path: Path):
    content = """## Introduction

### Subheader

First paragraph under subheader.

## Methods

Second paragraph.
"""
    path = _write(tmp_path / "test.md", content)
    passages = parse_file_sections(str(path), sections=["Introduction"])
    assert len(passages) == 1
    assert "Subheader" in passages[0].text
    assert "First paragraph" in passages[0].text