from __future__ import annotations

from pathlib import Path

from sem_debug.workspace_parser import InputDecl, read_context_md


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_valid_context_md(tmp_path: Path):
    content = """---
question: "Test question"
models:
  researcher_a: "test-model"
---

## Inputs

| Source | Section |
|--------|---------|
| 01_intro.md | Introduction |
| 02_data.md | Data |
"""
    path = _write(tmp_path / "CONTEXT.md", content)
    result = read_context_md(path)
    assert len(result) == 2
    assert result[0] == InputDecl(source="01_intro.md", section="Introduction")
    assert result[1] == InputDecl(source="02_data.md", section="Data")


def test_parse_no_inputs_table(tmp_path: Path):
    content = """---
question: "No inputs here"
---

## Background

Some background text.
"""
    path = _write(tmp_path / "CONTEXT.md", content)
    result = read_context_md(path)
    assert result == []


def test_parse_malformed_table(tmp_path: Path):
    content = """---
question: "Malformed"
---

## Inputs

This is not a table.
"""
    path = _write(tmp_path / "CONTEXT.md", content)
    result = read_context_md(path)
    assert result == []


def test_parse_section_optional(tmp_path: Path):
    content = """---
question: "Single column"
---

## Inputs

| Source |
|--------|
| 01_intro.md |
| 02_data.md |
"""
    path = _write(tmp_path / "CONTEXT.md", content)
    result = read_context_md(path)
    assert len(result) == 2
    assert result[0] == InputDecl(source="01_intro.md", section=None)
    assert result[1] == InputDecl(source="02_data.md", section=None)


def test_parse_empty_file(tmp_path: Path):
    path = _write(tmp_path / "CONTEXT.md", "")
    result = read_context_md(path)
    assert result == []