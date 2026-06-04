# NORTHSTAR.md — sem_debug v2 Build Reference

**Plan source:** `PLAN.md` (vetted, PLAN_REP.md resolved)  
**Codebase state:** 51/51 tests passing, `sem_debug/` package with 6 modules + 8 test files  
**Build order:** Phase 1 → Phase 2 → Phase 3 → Phase 4 (sequential, no skipping)  
**Comment policy:** Every public function, class, and module-level constant gets a docstring. Complex logic blocks (heuristics, fallbacks, regex) get inline comments. Comments explain *why*, not *what* — the code already says what.

---

## Design Constraints (non-negotiable)

| Constraint | Rationale |
|---|---|
| Default behavior unchanged | `--format` default is `markdown`. All Phase 1–4 CLI invocations work identically. |
| No breaking changes to `TraceResult` fields | `attributed`, `unattributed`, `verdict` stay as declared. Additive only. |
| Subprocess-only public contract | `__init__.py` stays empty. External callers use `sem_debug --format json`. |
| `workspace_parser.py` import-clean | Imports: `pathlib`, `re`, `typing`. No `parser.py`, `tracer.py`, or `matcher.py` imports. |
| Section extraction heuristic, never crash | Malformed `CONTEXT.md` → log warning to stderr, fallback to whole-file reading. |

---

## Comment Standards

**Docstring format (all public functions/classes):**
```python
def to_dict(self) -> dict:
    """Return a flat dict representation for JSON serialization.

    Keys: verdict.status, verdict.exit_code, stage, threshold,
          attributed (list of dicts), unattributed (list of dicts).
    Each match dict contains: passage_index, source_file, source_line_start,
    score, method ("tfidf" | "semantic").
    """
```

**Inline comment format (complex blocks):**
```python
# FALLBACK: If no Inputs table found, read the entire source file.
# This preserves the Phase 1–4 behavior for workspaces without CONTEXT.md.
```

**Rule:** If a function is >15 lines OR contains a conditional with >2 branches, it gets at least one inline comment explaining the branch rationale.

## Phase 1 — Structured Output (`--format json`)

### New code

#### `models.py` — add `to_dict()` methods

```python
def to_dict(self) -> dict:
    """Return a flat dict representation for JSON serialization.

    Keys: verdict.status, verdict.exit_code, stage, threshold,
          attributed (list of dicts), unattributed (list of dicts).
    Each match dict contains: passage_index, source_file, source_line_start,
    score, method ("tfidf" | "semantic").
    """

# Implementation notes:
# - Flatten Verdict into the top-level dict under keys "status" and "exit_code".
# - Convert Match and Passage dataclass instances into plain dicts with primitive values.
# - source_file must be str (already is), score must be float (round to 4 decimals).
# - method field: use match.method.value (Enum str) or the stored string.
```

**Add to:** `sem_debug/models.py`, inside `TraceResult` class.
**Signature:** `def to_dict(self) -> dict:`
**Return shape:**
```json
{
  "status": "CLEAN",
  "exit_code": 0,
  "stage": "synthesis",
  "threshold": 0.35,
  "attributed": [
    {
      "passage_index": 0,
      "source_file": "input_source_alpha.md",
      "source_line_start": 1,
      "score": 0.4821,
      "method": "tfidf"
    }
  ],
  "unattributed": [
    {
      "passage_index": 2,
      "best_failed_score": 0.12,
      "text_preview": "First 80 chars of passage text..."
    }
  ]
}
```

**Also add:** `Verdict.to_dict() -> dict` returning `{"status": self.status, "exit_code": self.exit_code}`. This is called by `TraceResult.to_dict()` but also available standalone.

---

#### `reporter.py` — add `render_json()`

```python
def render_json(trace_result: TraceResult) -> str:
    """Return a JSON string representation of the trace result.

    Uses TraceResult.to_dict() under the hood. Indent=2 for readability.
    """
```

**Add to:** `sem_debug/reporter.py`, after `render()`.
**Signature:** `def render_json(trace_result: TraceResult) -> str:`
**Implementation:** `return json.dumps(trace_result.to_dict(), indent=2)`
**Import needed:** `import json` at module top level (already imported in reporter.py per current codebase — verify first).

---

#### `cli.py` — add `--format` and `--json`

**Changes to `main()` argument parsing:**
- Add `--format {markdown,json}` argument. Default: `"markdown"`.
- Add `--json` as a boolean flag (store_true). When present, equivalent to `--format json`. If both `--json` and `--format` are provided, `--json` wins (or error — pick one, document it).
- Wire `--format` into the `trace()` call. When `format == "json"`, call `render_json()` instead of `render()`, print result to stdout.
- Wire `--report` to work with both formats. Existing behavior: `--report FILE` writes markdown to file. New behavior: when `--format json` and `--report FILE`, write JSON string to file. Stdout stays empty.

**Exit codes:** Unchanged. 0=CLEAN, 1=DRIFT, 2=BLOCKED (strict). `--format` does not affect exit codes.

**Help epilog update:** Add JSON schema description under exit codes. Example:
```
JSON output schema (sem_debug --format json):
  {
    "status": "CLEAN|DRIFT|BLOCKED",
    "exit_code": 0|1|2,
    "stage": "string",
    "threshold": float,
    "attributed": [...],
    "unattributed": [...]
  }
```

---

### Phase 1 Tests

#### `tests/test_json_output.py` (new file)

1. `test_trace_result_to_dict_structure` — assert exact keys exist, types are primitives.
2. `test_verdict_to_dict` — assert `{"status": "CLEAN", "exit_code": 0}`.
3. `test_render_json_returns_string` — call `render_json()` on a fixture `TraceResult`, assert `json.loads()` succeeds.
4. `test_cli_format_json_exit_0` — subprocess: `sem_debug output_clean.md --inputs input_source_alpha.md --format json`, assert valid JSON, exit 0.
5. `test_cli_format_json_exit_1` — subprocess: `sem_debug output_drift.md --inputs input_source_alpha.md --format json`, assert valid JSON, exit 1, `unattributed` list non-empty.
6. `test_cli_json_shorthand` — subprocess: `sem_debug output_clean.md --inputs input_source_alpha.md --json`, assert same as `--format json`.
7. `test_cli_report_with_json` — subprocess: `sem_debug output_clean.md --inputs input_source_alpha.md --format json --report out.json`, assert file written, stdout empty.

**Test count:** 7 new tests.

---

### Phase 1 Gates

| Gate | Command / Action | Expected |
|---|---|---|
| 1 | `pytest -x` | 58 passing (51 + 7 new) |
| 2 | `sem_debug fixtures/output_clean.md --inputs fixtures/input_source_alpha.md --format json` | Valid JSON, exit 0 |
| 3 | `sem_debug fixtures/output_drift.md --inputs fixtures/input_source_alpha.md --format json --report report.json` | File written, stdout empty |
| 4 | `python -c "import json; print(json.loads(open('report.json').read()).keys())"` | `['status', 'exit_code', 'stage', 'threshold', 'attributed', 'unattributed']` |

---

## Phase 2 — CONTEXT.md Awareness (`--context-md`)

### New code

#### `workspace_parser.py` (new module)

**File:** `sem_debug/workspace_parser.py`

```python
"""Parse ICM-style CONTEXT.md to discover declared input sections.

The Inputs table is a markdown table under the "Inputs" H2 section.
Each row has columns: Source, Section (optional).
If no Inputs table is found, the parser returns an empty list,
and the caller falls back to whole-file reading.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple


class InputDecl(NamedTuple):
    """A single declared input source with optional section name."""
    source: str
    section: str | None


def read_context_md(path: Path) -> list[InputDecl]:
    """Parse CONTEXT.md frontmatter and Inputs table.

    Returns a list of InputDecl tuples. Empty list if no Inputs table found.
    Never raises — malformed files return empty list with a warning printed
    to stderr (not logged; stderr is visible to CLI callers).
    """
```

**Implementation notes:**
- Read entire file as text.
- Skip YAML frontmatter (delimited by `---` lines).
- Find H2 header `## Inputs` (case-insensitive match on "Inputs", allow trailing text).
- Extract the first markdown table after that header, stopping at next H2 or EOF.
- Table rows: split on `|`, strip whitespace. Skip header row and separator row (`|---|---|`).
- Expected columns: Source, Section (optional). If only one column, Section is None.
- Return `[]` if no table found. Print warning to stderr: `Warning: no Inputs table in {path}`.
- **Import restriction:** Only `re`, `pathlib`, `typing` allowed. No `parser.py`, `tracer.py` imports.

---

#### `parser.py` — add `parse_file_sections()`

**Add to:** `sem_debug/parser.py`

```python
def parse_file_sections(path: Path, sections: list[str] | None = None) -> list[Passage]:
    """Parse a markdown file, optionally extracting only named H2 sections.

    If sections is None, behaves exactly like parse_file() — returns all passages.
    If sections is provided, only passages inside the named H2 sections are returned.
    A passage belongs to a section if it appears after the section's H2 header
    and before the next H2 header or EOF.

    Headers (H1-H6) merge with following paragraphs per AD-05. This rule applies
    within sections exactly as it does globally.
    """
```

**Implementation notes:**
- Reuse existing `parse_file()` logic where possible. Consider refactoring `parse_file()` to call `parse_file_sections(path, sections=None)` internally, or keep them separate if the logic divergence is too large.
- Section boundary detection: split file into lines, track `## Section Name` headers, collect passages only when `current_section in sections`.
- Code blocks and HTML comments skipped per AD-06 / AD-11 inside sections too.
- If a requested section name is not found in the file, print warning to stderr: `Warning: section '{name}' not found in {path}` and skip it.
- **Complexity:** If this function exceeds 30 lines, add inline comments for the state machine (tracking section membership across lines).

---

#### `tracer.py` — wire `--context-md`

**Add to:** `sem_debug/tracer.py`

```python
def trace(
    output_path: Path,
    input_paths: list[Path],
    stage: str = "synthesis",
    threshold: float = DEFAULT_THRESHOLD,
    semantic: bool = False,
    context_md: Path | None = None,
) -> TraceResult:
    """Trace attribution with optional CONTEXT.md for section-aware input loading.

    If context_md is provided, it is parsed for an Inputs table. Each declared
    source is resolved relative to the output_path's directory (or workspace
    root). If a section is declared, only that section is read from the source.
    If no Inputs table is found, all input_paths are read whole-file as before.
    """
```

**Implementation notes:**
- `context_md` parameter is optional. When `None`, behavior is identical to current `trace()`.
- When provided:
  1. Call `workspace_parser.read_context_md(context_md)` to get `list[InputDecl]`.
  2. For each `InputDecl`, resolve `source` to a `Path`. Resolution rule: relative to `context_md.parent` (the stage directory).
  3. If `InputDecl.section` is set, call `parse_file_sections(resolved_path, [section])`. If None, call `parse_file(resolved_path)`.
  4. Collect all passages into `input_passages` list passed to `match_passages()`.
  5. If `read_context_md()` returns `[]` (no Inputs table), fall back to reading all `input_paths` whole-file, exactly as before.
- **Inline comment required:** Explain the resolution rule (why `context_md.parent`, not `output_path.parent`).

---

#### `cli.py` — add `--context-md`

**Add argument:** `--context-md PATH` (optional). Passed through to `trace()`.

---

### Phase 2 Tests

#### `tests/test_workspace_parser.py` (new file)

1. `test_parse_valid_context_md` — fixture with frontmatter + Inputs table (2 sources, 1 with section). Assert 2 `InputDecl`, correct fields.
2. `test_parse_no_inputs_table` — fixture with frontmatter but no Inputs H2. Assert `[]`, warning to stderr.
3. `test_parse_malformed_table` — fixture with Inputs H2 but non-table content. Assert `[]`, warning to stderr.
4. `test_parse_section_optional` — fixture with single-column table (Source only). Assert `section is None`.
5. `test_parse_empty_file` — empty file. Assert `[]`, warning to stderr.

#### `tests/test_parser_sections.py` (new file)

1. `test_parse_file_sections_none` — `parse_file_sections(path, None)` identical to `parse_file(path)`.
2. `test_parse_single_section` — fixture with two H2 sections, request one. Assert passages only from that section.
3. `test_parse_multiple_sections` — request two sections, assert union of passages.
4. `test_parse_missing_section` — request non-existent section. Assert `[]` passages, warning to stderr.
5. `test_section_header_merge` — H2 inside a requested section merges with following paragraph per AD-05.

#### `tests/test_tracer_context.py` (new file)

1. `test_trace_with_context_md` — call `trace(..., context_md=fixture)` where fixture Inputs table points to existing input. Assert identical verdict to manual `input_paths`.
2. `test_trace_context_md_falls_back` — context_md with no Inputs table. Assert same as `input_paths` whole-file.

**Test count:** 5 + 5 + 2 = 12 new tests.

---

### Phase 2 Gates

| Gate | Command / Action | Expected |
|---|---|---|
| 1 | `pytest -x` | 70 passing (58 + 12 new) |
| 2 | `python -c "from sem_debug.workspace_parser import read_context_md"` | Import succeeds (no `parser.py`/`tracer.py` imported) |
| 3 | Subprocess with `--context-md` on fixture workspace | Same unattributed count as without |
| 4 | Subprocess with malformed `--context-md` | Does not crash, falls back to whole-file |

## Phase 3 — Clean Subprocess Contract for `research_loop`

### Changes

#### `models.py` — no new code, schema frozen by test

`TraceResult.to_dict()` and `Verdict.to_dict()` already added in Phase 1. No changes.

#### `cli.py` — help epilog + `--json` shorthand

**`--json` flag:** Already specified in Phase 1. If not yet added, add it now. If already added, verify it works.

**Help epilog update:** Under the exit codes section, append:
```
JSON output schema (--format json or --json):
  {
    "status": "CLEAN|DRIFT|BLOCKED",
    "exit_code": 0|1|2,
    "stage": "string",
    "threshold": float,
    "attributed": [
      {
        "passage_index": int,
        "source_file": "string",
        "source_line_start": int,
        "score": float,
        "method": "tfidf|semantic"
      }
    ],
    "unattributed": [
      {
        "passage_index": int,
        "best_failed_score": float,
        "text_preview": "string"
      }
    ]
  }
```

---

#### `tests/test_json_contract.py` (new file)

```python
"""Frozen contract test: to_dict() schema must not drift.

If this test fails, the JSON contract has changed and research_loop's
Trace.check() may break. Do not change to_dict() shape without updating
this test and the help epilog.
"""
```

**Test functions:**

1. `test_trace_result_dict_keys` — Build a `TraceResult` with 1 attributed, 1 unattributed. Call `.to_dict()`. Assert top-level keys: `status`, `exit_code`, `stage`, `threshold`, `attributed`, `unattributed`. Assert no extra keys.

2. `test_attributed_match_dict_keys` — Assert each attributed dict has: `passage_index`, `source_file`, `source_line_start`, `score`, `method`. Assert `method` is `"tfidf"` or `"semantic"`. Assert `score` is float (not Decimal, not string).

3. `test_unattributed_dict_keys` — Assert each unattributed dict has: `passage_index`, `best_failed_score`, `text_preview`. Assert `best_failed_score` is float. Assert `text_preview` is string with length <= 80.

4. `test_verdict_dict_keys` — Assert `Verdict.to_dict()` has exactly `status` and `exit_code`.

5. `test_method_semantic_preserved` — Build a `TraceResult` with a semantic match. Assert `method == "semantic"` in the attributed dict.

**Test count:** 5 new tests.

---

### Phase 3 Gates

| Gate | Command / Action | Expected |
|---|---|---|
| 1 | `pytest tests/test_json_contract.py -v` | 5 passing |
| 2 | `sem_debug --help` | Epilog shows JSON schema description |
| 3 | `pytest -x` (full suite) | 81 passing (76 + 5 new) |

---

## Phase 4 — Calibration & Section-Loading Tests

### Changes

#### `tests/fixtures/context_workspace/` (new fixture directory)

Create a minimal ICM-style workspace:
```
tests/fixtures/context_workspace/
  CONTEXT.md          # frontmatter + Inputs table pointing to 01_intro.md, 02_data.md
  01_intro.md         # H2 "Introduction" with 2 paragraphs
  02_data.md          # H2 "Data" with 2 paragraphs, H2 "Methods" with 1 paragraph
  output_full.md      # draft output referencing only the 4 paragraphs from Introduction + Data (clean)
  output_drift.md     # draft output with 1 new paragraph not in any declared section (drift)
```

**`01_intro.md` content:**
```markdown
## Introduction

Para 1 text here.

Para 2 text here.
```

**`02_data.md` content:**
```markdown
## Data

Para 3 text here.

Para 4 text here.

## Methods

Para 5 text here (not in Inputs table).
```

**`CONTEXT.md` content:**
```yaml
---
question: "Test question"
models:
  researcher_a: "test-model"
---

## Inputs

| Source | Section |
|--------|---------|
| 01_intro.md | Introduction |
| 02_data.md | Data |
```

---

#### `tests/test_calibration_sections.py` (new file)

1. `test_section_vs_wholefile_same_verdict` — Run `trace()` twice on `output_full.md`:
   - Once with `context_md=CONTEXT.md` (only "Introduction" and "Data" sections loaded)
   - Once without `context_md`, passing `01_intro.md` and `02_data.md` as `input_files`
   Assert same `verdict.status == "CLEAN"` both times.

2. `test_section_load_reduces_input_passages` — Run `trace()` with `context_md=CONTEXT.md` on `output_full.md`. The Inputs table declares only "Introduction" (2 paragraphs) and "Data" (2 paragraphs), while `02_data.md` has an extra "Methods" section (1 paragraph). Assert that the whole-file case includes 5 input passages and the section-filtered case includes 4.

3. `test_drift_detected_with_sections` — Run `trace()` with `context_md=CONTEXT.md` on `output_drift.md` (which contains a new paragraph not in any declared section). Assert `verdict.status == "DRIFT"`.

4. `test_semantic_json_combo` — Subprocess: `sem_debug output_drift.md --inputs 01_intro.md 02_data.md --context-md CONTEXT.md --semantic --format json`. Assert valid JSON, `method` field present. If semantic matching rescues a low-score match, `method` may be `"semantic"`.

**Test count:** 4 new tests.

---



### Phase 4 Gates

| Gate | Command / Action | Expected |
|---|---|---|
| 1 | `pytest -x` | 85 passing (81 + 4 new) |
| 2 | Section-loaded vs whole-file on fixture workspace | Same verdict, reduced input passage count |
| 3 | `--semantic --format json` combo | Valid JSON with `method` field |
| 4 | `--context-md` with malformed file | Does not crash, warning to stderr |

---

## Post-Build Test Count

| Phase | New Tests | Cumulative |
|---|---|---|
| Phase 1 | 7 | 58 |
| Phase 2 | 12 | 70 |
| Phase 3 | 5 | 81 |
| Phase 4 | 4 | 85 |

**Target total: 85 tests.**

