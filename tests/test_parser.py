from __future__ import annotations

from models import Passage
from parser import parse_file


def test_empty_file():
    result = parse_file("tests/fixtures/empty.md")
    assert result == []


def test_single_paragraph():
    result = parse_file("tests/fixtures/single_para.md")
    assert len(result) == 1
    p = result[0]
    assert p.text == "This is a single prose paragraph with no headers and no code blocks. It contains enough text to be meaningfully attributed to an input source. The quick brown fox jumps over the lazy dog several times before settling down for the evening."
    assert p.line_start == 1
    assert p.line_end == 1
    assert "single_para.md" in p.source_file


def test_headers_merged_with_prose():
    result = parse_file("tests/fixtures/with_headers.md")
    assert len(result) == 3
    assert "# Introduction" in result[0].text
    assert "introduction paragraph" in result[0].text
    assert result[0].line_start == 1
    assert result[0].line_end == 3
    assert "## Background" in result[1].text
    assert "background section" in result[1].text
    assert result[1].line_start == 5
    assert result[1].line_end == 7
    assert "## Results" in result[2].text
    assert "Key findings" in result[2].text
    assert result[2].line_start == 9
    assert result[2].line_end == 11


def test_code_blocks_skipped():
    result = parse_file("tests/fixtures/with_code.md")
    assert len(result) == 3
    assert "# Overview" in result[0].text
    assert "This document shows" in result[0].text
    assert result[0].line_start == 1
    assert result[0].line_end == 3
    assert "## Example" in result[1].text
    assert "Here is a sample code block" in result[1].text
    assert result[1].line_start == 5
    assert result[1].line_end == 7
    assert "prints a greeting" in result[2].text
    assert result[2].line_start == 14
    assert result[2].line_end == 14
    for p in result:
        assert "def hello" not in p.text
        assert "Hello, world" not in p.text


def test_header_only_returns_empty():
    result = parse_file("tests/fixtures/header_only.md")
    assert result == []
