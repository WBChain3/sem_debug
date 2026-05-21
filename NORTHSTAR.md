# NORTHSTAR.md — sem_debug Shipping Build Plan

**Branch:** shipping-prep
**Total tasks:** 4
**Test discipline:** `pytest -x` after every step that touches a `.py` file. Agent always stops after tests; operator decides to proceed. No auto-fixes on test failure.
**Positioning:** This tool targets the technical end of the ICM user spectrum and is designed to work in multi-agent multi-window Claude Code workflows as well as single-agent sequential ones.

---

## Phase 0 — Baseline Check

**Step 0.1** — Run `pytest -x` before any changes. Confirm 51 passing.
- If count is not 51, stop and report.

---

## Phase 1 — Cosmetic Fixes (Task 1)

All changes are import/variable cleanup with zero behavior change.

### Step 1.1 — parser.py: delete dead variable
**Action:** Remove line 34 (`comment_start = i`).
**Why:** Assigned but never referenced. Dead code.
**Verification:** `pytest -x` must pass.

### Step 1.2 — models.py: remove unused `field` import
**Action:** Change line 3 from `from dataclasses import dataclass, field` to `from dataclasses import dataclass`.
**Why:** No dataclass uses `field()`.
**Verification:** `pytest -x` must pass.

### Step 1.3 — tests/test_cli.py: remove unused `pytest` import
**Action:** Delete line 8 (`import pytest`).
**Why:** No pytest APIs used anywhere in file.
**Verification:** `pytest -x` must pass.

### Step 1.4 — tests/test_matcher.py: remove unused `pytest` import
**Action:** Delete line 3 (`import pytest`).
**Why:** No pytest APIs used anywhere in file.
**Verification:** `pytest -x` must pass.

### Step 1.5 — tests/test_parser.py: remove unused `Passage` import
**Action:** Delete line 3 (`from models import Passage`).
**Why:** `Passage` is never constructed or referenced by name in test body. Instances returned by `parse_file()` retain their runtime type.
**Verification:** `pytest -x` must pass.

### Step 1.6 — tracer.py: remove unused `Match` import, justify `Passage`
**Action:** Change line 3 from:
```python
from models import DEFAULT_THRESHOLD, Match, Passage, TraceResult, Verdict
```
to:
```python
from models import DEFAULT_THRESHOLD, Passage, TraceResult, Verdict
```
and add inline comment at line 16 (`input_passages: list[Passage] = []`) reading exactly:
```python
# retained: Passage used in type annotation on line 16; removing breaks mypy
```
**Why:** `Match` is never referenced in the file. `Passage` is required only for the type annotation on line 16. The explicit comment prevents a future agent from treating it as decorative and removing it.
**Verification:** `pytest -x` must pass.

### Step 1.7 — Phase 1 final gate
**Verification:** `python -c "from tracer import trace; print('OK')"`
**Verification:** `pytest -x` must pass with same count as Step 0.1.

---

## Phase 2 — Semantic Validation (Task 2)

Goal: Confirm Zone 2 paraphrase rescue works with real sentence-transformers embeddings.

### Step 2.1 — Install semantic dependencies
**Action:** `pip install -r requirements-semantic.txt`
**Why:** Provides `sentence-transformers` and `torch` needed for `--semantic` path.
**Verification:** `python -c "import sentence_transformers; print('OK')"`

### Step 2.2 — Manual CLI run on Zone 2 fixture
**Action:** Run:
```
python sem_debug.py tests/fixtures/output_draft.md --inputs tests/fixtures/input_source_alpha.md tests/fixtures/input_source_beta.md --semantic
```
**What to report:**
- Does the report show the Zone 2 passage (line 5) as **attributed** with `method="semantic"`?
- What is the exact score shown?
- Compare score to the TF-IDF best-failed score (around 0.1952) from the non-semantic run.

### Step 2.3 — Decision gate
- If Zone 2 score >= 0.35 and appears attributed → semantic rescue confirmed. Proceed.
- If Zone 2 score < 0.35 or remains unattributed → report actual score and behavior. User decides whether to adjust threshold or document limitation.
- If the process crashes → report traceback. User decides.

### Step 2.4 — Post-validation test gate
**Action:** `pytest -x` (with sentence-transformers now installed).
**Expected:** All 51 tests still pass. The `test_cli_semantic_flag_imports` test may switch branches internally but should not fail.

---

## Phase 3 — Installable Package (Task 3)

Goal: Make `sem_debug` installable via `pip install .` with a CLI entry point.

### Step 3.1 — Precondition check
**Action:** Confirm no `pyproject.toml` exists at workspace root.
- If one exists, read it and verify it does not already declare the entry point. If it does, document deviation.

### Step 3.2 — Create pyproject.toml
**Action:** Write `pyproject.toml` with:
- `[project]` metadata: name, version, description, authors (optional but good), Python requirement.
- `[project.dependencies]`: `scikit-learn`.
- `[project.scripts]` entry point: `sem_debug = sem_debug:main`.
- `[build-system]` with `setuptools` or `hatchling` as backend.
**Constraint:** Do NOT add extra metadata not needed for `pip install .` and `sem_debug --help`.
**Entry point note:** `main()` is confirmed present at line 10 in `sem_debug.py`, guarded by `if __name__ == "__main__"` at line 67. The entry point `sem_debug = sem_debug:main` is correct and safe.
**Verification:** `python -c "import pathlib; assert pathlib.Path('pyproject.toml').exists(); print('OK')"`

### Step 3.3 — pyproject.toml does not break tests
**Action:** `pytest -x` must pass with same count as before.
**Reason:** Adding packaging metadata should not change runtime behavior.

### Step 3.4 — Manual install verification
**Action:** In the current venv (or a fresh one if user prefers), run `pip install .` from workspace root.
**Verification:** `sem_debug --help` completes without error. Confirm the epilog shows exit codes.
- If `sem_debug` command not found on PATH after pip install, report immediately.

---

## Phase 3.5 — KNOWN_LIMITATIONS.md

**Action:** Write `KNOWN_LIMITATIONS.md` to repo root before Phase 4 begins.
**Why:** This file ships with the code. Findings from Phase 4 smoke tests may add to it, but the four baseline sections must exist first.
**Required sections:**

1. **Language and Environment Dependency**
   - `sem_debug` requires Python 3.8 or higher, required for from __future__ import annotations
   - Windows console default encoding (cp1252/cp437) cannot display U+2013 en dash. Terminal output may show replacement characters. The `--report FILE` path writes correct UTF-8 and is the recommended way to view output on Windows.

2. **Semantic Matching Experimental Status**
   - The `--semantic` flag requires `sentence-transformers` and downloads the `all-MiniLM-L6-v2` model on first use (~80 MB from HuggingFace). No semantic rescue has been empirically validated with real embeddings in this build. TF-IDF remains the validated default. Semantic behavior should be treated as experimental until validated.

3. **Single Stage Boundary Only**
   - `sem_debug` traces one output file against a set of input files. It does not compare draft N against draft N+1, track temporal drift across iterations, or instrument pipelines. Each invocation is an independent snapshot.

4. **Attribution Is Best-Match, Not Causal**
   - Output passages are linked to their highest-scoring input passage. When multiple inputs overlap, the tool picks one winner. It cannot distinguish faithful reproduction from accidental lexical overlap, and it cannot prove the agent actually read the input passage before writing the output. Attribution is heuristic proximity, not causal provenance.

**Verification:** `python -c "import pathlib; assert pathlib.Path('KNOWN_LIMITATIONS.md').exists(); print('OK')"`

---

## Phase 4 — Real Content Smoke Test (Task 4)

### Step 4.1 — Operator runs manual smoke test
The operator selects any real `output.md` and its declared `input.md` files from their own workflow.

**Action:** Run:
```
sem_debug <output_path> --inputs <input1> [input2 ...]
```
**What to observe and report:**
1. Does the report print without crashing?
2. Do the attributed passages make intuitive sense?
3. Do the unattributed passages represent actual drift/hallucination? Or are they false negatives (legitimate content that just had poor vocabulary overlap)?
4. Is the line-range formatting readable?
5. Any `?` characters in the terminal where en dashes should appear? (Known Windows console limitation — reported in KNOWN_LIMITATIONS.md section 1.)

### Step 4.2 — Findings gate
- No pass/fail threshold. Operator records observations.
- If any surprising behavior is found, it either informs a pre-ship patch or gets added to `KNOWN_LIMITATIONS.md`.

---

## Exit Gate — Ship Ready Checklist

All phases complete (or acknowledged as deferred by operator):

- [ ] `pytest -x` passes with zero failures
- [ ] 51 tests passing (or current count documented)
- [ ] Phase 1 cosmetic cleanup applied
- [ ] Phase 2 semantic rescue validated (score on record)
- [ ] `pyproject.toml` present; `pip install .` works; `sem_debug --help` works
- [ ] `KNOWN_LIMITATIONS.md` present with four required sections
- [ ] Phase 4 real content smoke test completed and findings documented
- [ ] No bare `except Exception`, no network calls in tests, typed exceptions only
- [ ] AD records updated if new decisions were made during build

---

## Rules for This Plan

1. **After every step that touches a `.py` file, run `pytest -x` and report pass/fail.**
2. **If `pytest -x` fails, STOP immediately.** Do not proceed to next step. Report failure to operator.
3. **Agent never fixes a test failure automatically.** Operator decides whether to investigate, patch, or skip.
4. **Between phases, user must explicitly approve advancement.** After a successful `pytest -x`, agent waits.
5. **No code changes in Phase 4** — observational only.
6. **If at any point test count changes from 51 without user-expected reason, flag it as a warning even if tests pass.**

---

*Phase-gate discipline. Verify second. Ship last.*
