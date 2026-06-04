# VET_REPORT_PHASE1.md — Pre-Build Vetting Report for Phase 1

**Date:** 2026-06-03  
**Phase:** Phase 1 — Structured Output (`--format json`)  
**Codebase state:** 61/61 tests passing (`pytest -x`).  
**Files changed:** `sem_debug/models.py`, `sem_debug/reporter.py`, `sem_debug/cli.py`, `tests/test_json_output.py` (new).  
**Deleted:** `SHIPPING_PLAN.md` (unrelated file, user/codecleanup).  

---

## Executive Summary

Phase 1 is **functionally complete and passing all tests**. The JSON output mode works end-to-end: `--format json`, `--json` shorthand, `--report` with JSON, and the CLI epilog documents the schema.  

**One semantic bug identified** in `TraceResult.to_dict()` that should be fixed before the JSON contract is frozen in Phase 3. Not a test blocker — all 61 tests pass — but will confuse programmatic consumers if shipped as-is.

**Verdict: PROCEED to Phase 2 after fixing MI-1.**

---

## Critical Blockers

*None.*

---

## High Issues

### HI-1 — `passage_index` in `to_dict()` is not a real passage index
- **File:** `sem_debug/models.py` lines 43-58
- **Observation:** `to_dict()` computes `passage_index` as a synthetic sequential number (`i` for attributed, `len(attributed) + len(unattributed)` for unattributed). This does **not** correspond to the passage's position in the original output file. A programmatic consumer expecting to locate the flagged passage by index will get the wrong passage.
- **Root cause:** `TraceResult` does not store the original `output_passages` list. `tracer.py` parses it on line 15 but never includes it in the `TraceResult` constructor.
- **Fix:** Add `output_passages: list[Passage] | None = None` to `TraceResult` (additive, not breaking — dataclass field with default). Populate it in `tracer.trace()`. In `to_dict()`, build a `passage_to_index` map and use it for both attributed and unattributed dicts. See MI-1 for implementation.
- **Why this matters:** The JSON contract is intended for `research_loop`'s `Trace.check()` to consume programmatically. Wrong indices produce wrong diagnostics.

---

## Medium Issues

### MI-1 — `source_passage_index` uses line number, not index
- **File:** `sem_debug/models.py` line 47
- **Observation:** `"source_passage_index": m.input_passage.line_start` assigns a **line number** to a field named **index**. The name promises an array index (0, 1, 2...), the value is a 1-based line number. This is misleading.
- **Fix:** Rename the JSON key to `source_line_start` (matches AD-08: line numbers are 1-based). This is a contract change — do it now before Phase 3 freezes the schema. Update NORTHSTAR.md accordingly.
- **Alternative:** Keep the name and compute a real source passage index. Harder because `Match` doesn't store the source passage's list position.

### MI-2 — `typing.Any` added to models.py
- **File:** `sem_debug/models.py` line 4
- **Observation:** `typing.Any` is imported for the `to_dict()` return annotation. The codebase has avoided broad typing imports before. `Any` weakens type safety.
- **Fix:** Replace `dict[str, Any]` with `dict[str, str | int | float | list[dict]]`. The actual value types are known. This is a 1-line change with no runtime effect.

### MI-3 — Phase 3 contract tests pulled into Phase 1
- **File:** `tests/test_json_output.py` lines 70-79
- **Observation:** `test_verdict_dict_keys` and `test_verdict_to_dict` were specified in NORTHSTAR.md as Phase 3 tests. They appear in Phase 1's test file. This is harmless — more coverage is good — but means Phase 3's `test_json_contract.py` will need distinct tests or may be redundant.
- **Fix:** In Phase 3, write `test_json_contract.py` to test the **frozen shape** — i.e., assert that adding a new field to `to_dict()` would fail the test. The current Phase 1 tests verify correctness; Phase 3 tests should verify stability.

---

## Low / Polish

### LI-1 — `--json` override not tested for conflict case
- **File:** `tests/test_json_output.py`
- **Observation:** No test verifies behavior when both `--json` and `--format markdown` are passed. The code does `output_format = "json" if args.json else args.format` which makes `--json` win. Reasonable but untested.
- **Fix:** Add one test: `test_cli_json_overrides_format` with `--format markdown --json`, assert JSON output.

### LI-2 — `test_cli_report_with_json` writes to fixtures dir
- **File:** `tests/test_json_output.py` line 130
- **Observation:** Temp file `tests/fixtures/tmp_report.json` is written inside the fixtures directory. Not ideal — should use `tempfile` or `tmp_path`.
- **Fix:** Use `tmp_path` fixture (pytest built-in) instead of hardcoded path. Not urgent.

### LI-3 — Help epilog uses raw string with `\n` escapes
- **File:** `sem_debug/cli.py` lines 14-24
- **Observation:** The epilog string uses explicit `\n` concatenation. This is correct argparse behavior but slightly hard to read.
- **Fix:** Use a triple-quoted string or dedent for readability. Not urgent.

---

## Test Count

| Phase | Expected | Actual | Delta |
|---|---|---|---|
| Phase 1 (new) | 7 | 10 | +3 (attributed keys, unattributed keys, verdict dict keys pulled from Phase 3) |
| Prior (Phase 1-4) | 51 | 51 | — |
| **Total** | **58** | **61** | **+3** |

All 61 passing. No regressions.

---

## Gate Check

| Gate | Status | Evidence |
|---|---|---|
| 1. `pytest -x` all 51 prior tests pass | ✅ | 51/51 confirmed |
| 2. `sem_debug --format json` returns valid JSON, exit 0/1 | ✅ | `test_cli_format_json_exit_0/1` pass |
| 3. `--report` with JSON writes file, stdout empty | ✅ | `test_cli_report_with_json` pass |
| 4. JSON schema keys correct | ⚠️ | Keys correct but `passage_index` semantic wrong (HI-1) |

---

## Recommended Fix Order (before Phase 2)

1. **MI-2** (1 min): Replace `dict[str, Any]` with explicit union type.
2. **MI-1** (5 min): Rename `source_passage_index` → `source_line_start` in `to_dict()` and update tests.
3. **HI-1** (15 min): Add `output_passages` to `TraceResult`, populate in `tracer.py`, fix `passage_index` computation in `to_dict()`, update tests to assert real indices.
4. **LI-1** (5 min): Add `--json` override test.

**Total: ~30 minutes.** All tests should still pass after fixes.

---

## Risk for Phase 2

| Risk | Mitigation |
|---|---|
| `tracer.py` changes from HI-1 fix may conflict with Phase 2 `context_md` param addition | Both are additive. No overlap in logic. Merge cleanly. |
| `workspace_parser.py` import restriction (no `parser.py`) | Enforced by code review. If CODE violates, reject. |

---

*Read first. Verify second. Ship last.*
