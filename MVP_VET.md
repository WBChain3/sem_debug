# MVP Vetting Report — sem_debug

**Date:** 2026-05-21
**Scope:** Full codebase, all 51 tests, all `.py` source files, all fixtures, CLI smoke tests
**Result:** 51/51 tests pass. Phase 1–4 structurally complete. Action required before shipping.

---

## Executive Summary

The codebase is functionally correct and structurally sound. No critical safety blockers. One **high-severity latent bug** (HI-1: mutable `Verdict` mutation) must be fixed before shipping. One **medium encoding issue** (LI-2) affects Windows terminal output quality. All other findings are cosmetic or architectural polish.

| Severity | Count | Status |
|---|---|---|
| Critical | 0 | — |
| High | 3 | 1 must fix before ship |
| Medium | 5 | Acceptable for MVP |
| Low | 3 | Polish / cosmetic |

---

## Issues

### HI-1 — Verdict object mutated in-place in CLI (side effect leak)
**File:** `sem_debug.py`, lines 52–54
**Severity:** High
**Description:** `Verdict` is a mutable dataclass. The CLI mutates it in-place when `--strict` promotes DRIFT to BLOCKED:
```python
verdict.status = "BLOCKED"
verdict.exit_code = 2
```
If downstream code ever holds a reference to the original `Verdict` returned by `tracer.trace()`, it will observe the mutated state unexpectedly.
**Fix:** Replace with immutable assignment:
```python
if args.strict and verdict.status == "DRIFT":
    verdict = Verdict(status="BLOCKED", exit_code=2)
```
**MVP gate:** Must fix before ship.

### HI-2 — Unused `comment_start` variable in parser (dead code)
**File:** `parser.py`, line 34
**Severity:** Medium-High (noise/confusion risk)
**Description:** `comment_start = i` is assigned inside HTML comment detection but never referenced. The multiline comment logic works correctly via `comment_ranges`, but this variable is scaffolding residue.
**Fix:** Delete line 34 (`comment_start = i`).
**MVP gate:** Cosmetic, but should be cleaned.

### HI-3 — `en_dash` string redefined inside loops
**File:** `reporter.py`, lines 28, 51
**Severity:** Low
**Description:** `en_dash = "\u2013"` is redefined on every loop iteration for both matched and unattributed passages. Redundant but not incorrect. A module-level constant would be cleaner.
**Fix:** Move to top-level constant `EN_DASH = "\u2013"`.
**MVP gate:** Polish, not a blocker.

---

### MI-1 — Unused `field` import in models.py
**File:** `models.py`, line 3
**Severity:** Medium
**Description:** `from dataclasses import dataclass, field` — `field` is never used.
**Fix:** `from dataclasses import dataclass`
**MVP gate:** Acceptable for MVP.

### MI-2 — Unused `pytest` import in test_cli.py
**File:** `tests/test_cli.py`, line 8
**Severity:** Medium
**Description:** `import pytest` but no pytest APIs used (no marks, no fixtures, no `pytest.raises`).
**Fix:** Remove the import.
**MVP gate:** Acceptable for MVP.

### MI-3 — Unused `pytest` import in test_matcher.py
**File:** `tests/test_matcher.py`, line 3
**Severity:** Medium
**Description:** `import pytest` but no pytest APIs used.
**Fix:** Remove the import.
**MVP gate:** Acceptable for MVP.

### MI-4 — Unused `Passage` import in test_parser.py
**File:** `tests/test_parser.py`, line 3
**Severity:** Medium
**Description:** `Passage` is imported explicitly but never constructed in test body.
**Fix:** Remove the import.
**MVP gate:** Acceptable for MVP.

### MI-5 — Unused imports in tracer.py
**File:** `tracer.py`, line 3
**Severity:** Medium
**Description:** `Match` and `Passage` are imported but not directly referenced in the function body.
**Fix:** Keep if used for type annotations; otherwise remove.
**MVP gate:** Acceptable for MVP.

---

### LI-1 — Mixed path separators in markdown output
**File:** `reporter.py` / `parser.py`
**Severity:** Low
**Description:** On Windows, `Inputs:` line uses forward slashes (from raw CLI args) while `Source:` lines use backslashes (from `pathlib.Path` normalization). Example:
```
Inputs: tests/fixtures/input_source_alpha.md, tests/fixtures/input_source_beta.md
Source: tests\fixtures\input_source_alpha.md (lines 1–1)
```
**Impact:** Cosmetic. Markdown renders correctly. Paths are semantically equivalent.
**Fix:** Normalize `source_file` in `parser.py` to forward slashes, or normalize CLI args before passing to `tracer.trace()`.
**MVP gate:** Acceptable for MVP.

### LI-2 — Windows stdout encoding mangles en dash (U+2013)
**File:** `reporter.py` / `sem_debug.py`
**Severity:** Low
**Description:** `sys.stdout` default encoding on Windows console cannot encode U+2013. The `print(report)` call renders `lines 1–1` as `lines 1?1` or `lines 1?1` depending on codepage. The `--report` file path writes correct UTF-8 and is unaffected.
**Fix:** Add `sys.stdout.reconfigure(encoding="utf-8")` in `sem_debug.py` before `print(report)` (Python 3.7+).
**MVP gate:** Terminal-only cosmetic; `--report` output is correct. Acceptable for MVP if documented.

### LI-3 — `test_cli_semantic_flag_imports` weak dual-branch logic
**File:** `tests/test_cli.py`, lines 104–118
**Severity:** Low
**Description:** The test branches on whether `sentence-transformers` is installed, but neither branch validates actual semantic matching behavior. The "not installed" branch simply asserts `returncode != 0`.
**Impact:** If `sentence-transformers` is later installed, the test silently switches branches without warning that the semantic matching path has never been validated.
**Fix:** Add a dedicated semantic calibration test once the dependency is installed.
**MVP gate:** Acceptable for MVP since semantic is opt-in.

---

## Safety Checklist

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | No `subprocess`, `exec()`, `eval()` in application logic | ✅ PASS | `subprocess` is only in `test_cli.py` |
| 2 | No network calls in tests | ✅ PASS | All fixtures disk-based; no HTTP |
| 3 | No bare `except Exception` anywhere | ✅ PASS | `except ValueError` in matcher; `except ModuleNotFoundError` in semantic branch |
| 4 | All typed exceptions, never swallowed | ✅ PASS | See above |
| 5 | Static fixtures loaded from disk | ✅ PASS | All in `tests/fixtures/` |
| 6 | Empty inputs produce safe defaults | ✅ PASS | Empty corpus → `matched=[], unattributed=[(p, 0.0)]` |
| 7 | No `__init__.py` anywhere | ✅ PASS | Only `conftest.py` |
| 8 | No live API calls in production code | ✅ PASS | `sentence-transformers` model download only on `--semantic` flag |

---

## Architecture Checklist

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | Code matches plan structure | ✅ PASS | All Phase 1–4 files match PHASE4_NS_REV.md |
| 2 | Module independence | ✅ PASS | Only `models.py` is shared; no circular imports |
| 3 | No duplicated logic | ✅ PASS | Formatting lives only in `reporter.py` |
| 4 | Config in constants, not inline | ✅ PASS | `DEFAULT_THRESHOLD` in `models.py` |
| 5 | Exit codes defined and enforced | ✅ PASS | 0, 1, 2; manual validation prevents argparse exit-2 collision |
| 6 | Path contract preserved | ✅ PASS | CLI does not resolve to absolute before `tracer.trace()` |
| 7 | Report format matches spec exactly | ✅ PASS | Verified by 18 reporter tests + smoke tests |
| 8 | Semantic branch isolated to matcher | ✅ PASS | `tracer.py` passes flag through only |
| 9 | `source_file` is relative path | ⚠️ RISK | Enforced by convention (caller passes relative), not by code |

---

## Module Dependency Graph

```
sem_debug.py
├── tracer.py
│   ├── parser.py ──→ models.py
│   └── matcher.py ──→ sklearn, models.py
├── reporter.py ──→ models.py
└── tracer.py (calls trace, render)
```

**DAG is acyclic.** `models.py` is a leaf. Good separation of concerns.

---

## Test Coverage Summary

| Test File | Count | Purpose |
|---|---|---|
| `test_parser.py` | 5 | Empty file, single para, headers merged, code blocks, header-only |
| `test_matcher.py` | 9 | Empty input, core matching, best-match selection, below-threshold, properties, edge cases |
| `test_matcher_calibration.py` | 3 | Zone 1 (high overlap), Zone 2 (paraphrase), Zone 3 (unrelated) |
| `test_models.py` | 1 | DEFAULT_THRESHOLD value |
| `test_tracer.py` | 6 | Drift, clean, stage, best-failed score, empty inputs, path preservation |
| `test_reporter.py` | 18 | Headers, sections, quoted text, en dash, scores, verdict block, presence/absence conditionals |
| `test_cli.py` | 8 | Exit codes (0,1,2), stage flag, threshold flag, report file, semantic import, missing inputs |
| **Total** | **51** | **51 passing, 0 failing** |

---

## Exit Gate (Phase 4) — Status

| # | Condition | Status | Notes |
|---|---|---|---|
| 1 | `pytest -x` zero failures | ✅ | 51 passed |
| 2 | `--help` exits clean with all flags | ✅ | Verified |
| 3 | Smoke tests: CLEAN=0, DRIFT=1, BLOCKED=2 | ✅ | Verified |
| 4 | `requirements.txt` with `scikit-learn` | ✅ | Present |
| 5 | `requirements-semantic.txt` with deps | ✅ | Present |
| 6 | No `parser.py` modifications | ✅ | Unchanged since Phase 2 |
| 7 | `matcher.py` limited to semantic ext | ✅ | Lines 49–82 added only |

---

## Drift Tracking

1. **What changed that the plan did not predict?**
   - `sem_debug.py` mutates `Verdict` in-place (HI-1). Plan did not specify immutability, but side effects are a latent bug.
   - `parser.py` contains an unused `comment_start` variable (HI-2) — residue from Phase 1 scaffolding.

2. **What assumptions turned out to be wrong?**
   - Assumption: Windows console handles UTF-8 en dash (LI-2). It does not.
   - Assumption: `pytest` imports were harmless (MI-2, MI-3). They are, but they are noise.

3. **Is the drift acceptable for MVP?**
   - HI-1 is **not acceptable** — must fix before ship.
   - HI-2, MI-1–5, LI-1–3 are all acceptable for MVP but should be cleaned in a polish pass.

---

## Recommendations Before Shipping

### Must do (blocks ship)
1. **HI-1:** Replace in-place `Verdict` mutation in `sem_debug.py` with immutable assignment:
   ```python
   verdict = Verdict(status="BLOCKED", exit_code=2)
   ```

### Should do (cleanliness)
2. **HI-2:** Remove `comment_start = i` from `parser.py` line 34.
3. **MI-1:** Remove unused `field` import from `models.py`.
4. **MI-2–4:** Remove unused `pytest`/`Passage` imports from test files.
5. **MI-5:** Remove or justify unused `Match`/`Passage` imports in `tracer.py`.

### Nice to have (polish)
6. **LI-1:** Normalize path separators in `parser.py` (replace backslashes with forward slashes) or in CLI before passing paths.
7. **LI-2:** Add `sys.stdout.reconfigure(encoding="utf-8")` in `sem_debug.py` before stdout print.
8. **LI-3:** Add a calibrated semantic test once `sentence-transformers` is installed (future Phase 4+ work).

---

## Verdict

**PROCEED after fixing HI-1.**

The codebase is robust, well-tested, and matches the plan. One high-severity side-effect bug is the sole blocker to shipping. All other findings are cosmetic or polish.

**Test count:** 51/51 passing
**Drift count:** 2 (HI-1, HI-2)
**Blockers to ship:** 1 (HI-1)

*Read first. Verify second. Ship last.*
