# NORTHSTAR.md — Build Plan

## Phase 1 Steps

### Step 1.1 — `tests/conftest.py`
Action: Create `tests/conftest.py` that inserts the workspace root into `sys.path` so test modules can import `models` and `parser` without `__init__.py` packages.
Verification: `python -m pytest tests/ --co -q` (must collect 0 tests without ImportError).

### Step 1.2 — `models.py`
Action: Create `models.py` in the project root with the four dataclasses (`Passage`, `Match`, `TraceResult`, `Verdict`) and the named constant `DEFAULT_THRESHOLD = 0.35`.
Verification: `python -c "from models import Passage, Match, TraceResult, Verdict, DEFAULT_THRESHOLD; assert DEFAULT_THRESHOLD == 0.35; print('OK')"`

### Step 1.3 — `tests/test_models.py`
Action: Create `tests/test_models.py`. Import `models` and write a single test that asserts `DEFAULT_THRESHOLD` equals `0.35`.
Verification: `pytest tests/test_models.py -x`

### Step 1.4 — `tests/fixtures/empty.md`
Action: Create `tests/fixtures/empty.md` as a zero-byte file.
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/empty.md'); assert p.exists() and p.read_bytes() == b''; print('OK')"`

### Step 1.5 — `tests/fixtures/single_para.md`
Action: Create `tests/fixtures/single_para.md` containing exactly one blank-line-delimited prose paragraph and no headers or code blocks.
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/single_para.md'); assert p.exists() and len(p.read_text().strip().split('\n\n')) == 1; print('OK')"`

### Step 1.6 — `tests/fixtures/with_headers.md`
Action: Create `tests/fixtures/with_headers.md` containing at least one markdown header (`# ` or `## `) followed immediately by a prose paragraph on subsequent lines, with blank lines between sections.
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/with_headers.md'); t = p.read_text(); assert '# ' in t and '\n\n' in t; print('OK')"`

### Step 1.6b — `tests/fixtures/header_only.md`
Action: Create `tests/fixtures/header_only.md` containing only markdown headers (`# ` and/or `## `) with no prose paragraphs and no code blocks.
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/header_only.md'); t = p.read_text(); assert '# ' in t and t.strip() != ''; print('OK')"`

### Step 1.7 — `tests/fixtures/with_code.md`
Action: Create `tests/fixtures/with_code.md` containing at least one fenced code block (triple backticks) with content inside, surrounded by prose paragraphs.
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/with_code.md'); assert p.exists() and '\`\`\`' in p.read_text(); print('OK')"`

### Step 1.8 — `parser.py`
Action: Create `parser.py` exposing `parse_file(path: str) -> list[Passage]`. It must read the file, split it into blank-line-delimited passages, skip fenced code blocks entirely (silently, do not emit passages for them), merge headers with the paragraph that follows them, use 1-based line numbers for `line_start` and `line_end`, store the relative path from workspace root in `source_file`, and return `[]` for empty input.
Verification: `python -c "from parser import parse_file; result = parse_file('tests/fixtures/empty.md'); assert result == [], f'Expected [] got {result}'; print('OK')"`

### Step 1.9 — `tests/test_parser.py`
Action: Create `tests/test_parser.py`. Import `models` and `parser`. Write tests covering: `empty.md` returns `[]`; `single_para.md` yields exactly one `Passage` with text matching the paragraph and 1-based line numbers spanning the file; `with_headers.md` yields passages where headers are merged with their following paragraph and `line_start`/`line_end` are correct; `with_code.md` yields only prose passages and no code-block content appears in any `Passage.text`; `header_only.md` returns `[]` (safe default, not a crash or partial passage).
Verification: `pytest tests/test_parser.py -x`

---

## Resolutions Applied from PLAN.md Ambiguities

- **Code blocks:** Skip silently (Constraints overrule Phase 1 parenthetical).
- **Chunking:** Blank-line-delimited paragraphs. Sentence-level too granular for TF-IDF at this corpus size; sliding windows add unneeded complexity.
- **Headers:** Merge with the following paragraph; never standalone passages. A header without its body is not meaningfully attributable.
- **Model tests:** Separate thin file (`test_models.py`) asserting the named constant. Keeps test files single-responsibility.
- **Parser function:** `parse_file(path: str) -> list[Passage]`.
- **`source_file`:** Relative path from workspace root. Matches the report example and keeps traces portable.
- **Line numbering:** 1-based. Matches the report example and how humans read files.
- **`tests/` packaging:** `conftest.py` with `sys.path` insert; no `__init__.py`. Keeps it flat and simple.
