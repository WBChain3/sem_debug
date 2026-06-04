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
        "source_passage_index": int,
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

2. `test_attributed_match_dict_keys` — Assert each attributed dict has: `passage_index`, `source_file`, `source_passage_index`, `score`, `method`. Assert `method` is `"tfidf"` or `"semantic"`. Assert `score` is float (not Decimal, not string).

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
| 3 | `pytest -x` (full suite) | 75 passing (70 + 5 new) |

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
  output_full.md      # draft output referencing all 5 paragraphs (clean)
  output_drift.md     # draft output with 1 new paragraph (drift)
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

1. `test_section_vs_wholefile_same_verdict` — Run `trace()` with `--context-md` (only "Introduction" and "Data" sections) and without (whole-file). Assert same `verdict.status` on `output_full.md`.

2. `test_section_load_reduces_input_passages` — Run `trace()` with `--context-md` on `02_data.md` (which has "Data" + "Methods" sections, but only "Data" is declared). Assert `len(input_passages)` < whole-file count.

3. `test_drift_detected_with_sections` — Run `trace()` with `--context-md` on `output_drift.md`. Assert `verdict.status == "DRIFT"`.

4. `test_semantic_json_combo` — Run `sem_debug output_drift.md --inputs ... --context-md ... --semantic --format json`. Assert valid JSON, `method` field present, `method == "semantic"` for any rescued match.

**Test count:** 4 new tests.

---

#### `tests/test_cli.py` — add new CLI tests

Append to existing `tests/test_cli.py`:

1. `test_cli_format_json` — already in Phase 1 tests. If not added there, add here.
2. `test_cli_context_md` — subprocess with `--context-md`, assert valid markdown report (default format).
3. `test_cli_context_md_json_combo` — subprocess with `--context-md --format json`, assert valid JSON.

**Test count:** 3 new tests (if not already covered in Phase 1).

---

### Phase 4 Gates

| Gate | Command / Action | Expected |
|---|---|---|
| 1 | `pytest -x` | 79 passing (75 + 4 new, or 75 + 3 if cli tests already counted) |
| 2 | Section-loaded vs whole-file on fixture workspace | Same verdict, reduced input passage count |
| 3 | `--semantic --format json` combo | Valid JSON with `method` field |
| 4 | `--context-md` with malformed file | Does not crash, warning to stderr |

---

## Post-Build Test Count

| Phase | New Tests | Cumulative |
|---|---|---|
| Phase 1 | 7 | 58 |
| Phase 2 | 12 | 70 |
| Phase 3 | 5 | 75 |
| Phase 4 | 4 | 79 |

**Target total: 79 tests.**

