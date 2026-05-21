# PHASE4_NS.md — Build Plan Phase 4
# CLI, Semantic Extension, and Integration

Source of truth for Phase 4. CODE reads this before touching any file.
Run `pytest -x` after every step. Do not proceed to the next step if any test fails.

---

## Carry-Forward Decisions

These are settled. Do not re-decide them.

- `parse_file(path: str) -> list[Passage]` is the parser contract.
- `match_passages` returns `tuple[list[Match], list[tuple[Passage, float]]]`.
- `semantic: bool = False` is accepted by `match_passages` and `tracer.trace`.
- Verdict at the library layer is `CLEAN` or `DRIFT` only (exit 0 / 1).
- `BLOCKED` (exit 2) and `--strict` promotion live in the CLI layer only.
- `source_file` on every Passage is a relative path from workspace root.
- Line numbers are 1-based.
- No `__init__.py` anywhere. `conftest.py` handles sys.path.
- Typed exceptions only. Never bare `Exception`.
- No network calls in any test. All fixtures are disk-based static files.
- All fixtures live in `tests/fixtures/`.

Architectural decisions governing Phase 4: AD-01, AD-02, AD-03, AD-07,
AD-08, AD-09, AD-11, AD-12, AD-13. Read ARCHITECT_DEC.md if any decision
below is unclear.

---

## Resolved Before Phase 4 Begins

### R-1: `tests/fixtures/output_clean.md`
**Status:** Created in Phase 3, Step 3.0. Not repeated in Phase 4.
**Verification:** Already passing in `test_tracer.py::test_clean_case`.

### R-2: `models.py` signatures aligned
**Status:** Fixed during Phase 3 pre-build vetting.
- `TraceResult.unattributed` is `list[tuple[Passage, float]]`
- `Verdict` has only `status: str` and `exit_code: int`

---

## Ambiguities Closed for Phase 4

| # | Ambiguity | Resolution |
|---|---|---|
| 2 | `--json` flag | **OUT of MVP.** CLI outputs markdown only. No JSON mode in Phase 4. If requested later, it is a new feature, not a plan gap. |
| 3 | `BLOCKED` semantics | **Only `--strict` triggers BLOCKED.** There is no natural count/ratio threshold for BLOCKED independent of `--strict`. The CLI computes: if `--strict` is set and `verdict.status == "DRIFT"`, promote to `BLOCKED` (exit 2). |
| 5 | `--strict` + semantic interaction | **Semantic-matched passages count as attributed.** If `--semantic` rescues a passage, it is no longer unattributed. Therefore `--strict` cannot fire on that passage. `--strict` checks the final `Verdict` after all matching passes complete. |
| 6 | Semantic branch location | **In `matcher.py` only.** `tracer.trace` passes `semantic=True` through to `match_passages`. All second-pass logic lives inside the matcher. `tracer.py` does not branch on the flag. |
| 10 | Exit code 2 from `--strict` | **Confirmed:** `--strict` is the *only* path to `BLOCKED`. This is acceptable and must be documented in the CLI help text. |

---

## Step 4.0 — `requirements.txt`

**Action:** Create `requirements.txt` in the workspace root. List exactly:

```
scikit-learn
```

This was a Phase 2 carry-over; it must exist before Phase 4 CLI smoke tests.

**Verification:**
```
python -c "import pathlib; t = pathlib.Path('requirements.txt').read_text(); assert 'scikit-learn' in t; print('OK')"
```

---

## Step 4.1 — `matcher.py` (semantic extension)

**Action:** Edit `matcher.py` so that when `semantic=True`, after the TF-IDF
pass completes, any passage in `unattributed` is re-encoded with
`sentence-transformers` and rescored.

Implementation requirements:

1. If `semantic=False`, behavior is unchanged from Phase 2/3.
2. If `semantic=True`:
   a. After the TF-IDF loop, collect all `unattributed` passage texts into a list.
   b. Import `sentence_transformers` (top-level import is acceptable; failure
      will be caught below).
   c. Encode unattributed passages and all input passages with
      `sentence-transformers.SentenceTransformer('all-MiniLM-L6-v2')`.
   d. Compute cosine similarity between unattributed embeddings and input embeddings.
   e. For each unattributed passage, if its best semantic score >= `threshold`,
      create a `Match` with `method="semantic"`, `score=round(best_score, 4)`,
      and move it from `unattributed` to `matched`.
   f. Passages failing both TF-IDF and semantic remain in `unattributed` with
      their **TF-IDF best-failed score unchanged**. The semantic score is used
      for attribution decision only; the float in the tuple stays the TF-IDF score.
3. Graceful fallback: if `sentence-transformers` is not installed, raise a typed
   exception with a clear user-facing message. Do **not** silently fall back to TF-IDF.
   The exception type must not be bare `Exception`. A custom exception or
   `ImportError` with a descriptive message is acceptable.

**Verification:**
```
python -c "from matcher import match_passages; print('OK')"
```

Then run:
```
pytest -x
```
All 43 existing tests must still pass (semantic flag is False by default).

---

## Step 4.2 — `requirements-semantic.txt`

**Action:** Create `requirements-semantic.txt` in the workspace root. List exactly:

```
sentence-transformers
torch
```

**Verification:**
```
python -c "import pathlib; t = pathlib.Path('requirements-semantic.txt').read_text(); assert 'sentence-transformers' in t and 'torch' in t; print('OK')"
```

---

## Step 4.3 — `sem_debug.py` (CLI entry point)

**Action:** Create `sem_debug.py` in the workspace root as the CLI entry point.

Argument parsing must support:

```
python sem_debug.py <output_file> --inputs <file1> [file2 ...]
```

Optional flags:
- `--stage TEXT` — passed to `tracer.trace()`
- `--threshold FLOAT` — passed to `tracer.trace()`
- `--semantic` — passed to `tracer.trace()`
- `--report FILE` — write markdown report to FILE instead of stdout
- `--strict` — promotes DRIFT to BLOCKED (exit 2)

Implementation requirements:

1. Use `argparse` from the standard library.
2. `--inputs` is required (at least one file). Error clearly if missing.
3. Call `tracer.trace()` with the parsed arguments.
4. Call `reporter.render()` with the returned `TraceResult` and `Verdict`.
5. If `--strict` is set and `verdict.status == "DRIFT"`, override to
   `BLOCKED` with `exit_code=2`.
6. If `--report` is provided, write the markdown string to that file path.
   Otherwise, print to stdout.
7. Exit with the final exit code (`0`, `1`, or `2`).
8. Do **not** resolve paths to absolute before passing to `tracer.trace()`.
   Preserve the exact strings the user provided to maintain AD-07 (relative
   paths in reports). See Risk R-3 below.
9. Help text must document the three exit codes: 0=CLEAN, 1=DRIFT, 2=BLOCKED.

**Verification:**
```
python sem_debug.py --help
```
Must complete without error and show all flags.

---

## Step 4.4 — `tests/test_cli.py`

**Action:** Create `tests/test_cli.py`. Use `subprocess.run` to invoke
`python sem_debug.py` with fixture paths. No direct imports of `tracer` or
`reporter` — test the CLI as a black-box process.

Tests:

**test_cli_clean_exit_0**
Invoke with `output_clean.md` and both input sources.
- Assert `returncode == 0`.
- Assert stdout contains `"Status: CLEAN"`.
- Assert stdout contains `"Verdict"`.

**test_cli_drift_exit_1**
Invoke with `output_draft.md` and both input sources.
- Assert `returncode == 1`.
- Assert stdout contains `"Status: DRIFT"`.

**test_cli_strict_blocked_exit_2**
Invoke with `output_draft.md`, both input sources, and `--strict`.
- Assert `returncode == 2`.
- Assert stdout contains `"Status: BLOCKED"`.

**test_cli_report_writes_to_file**
Invoke with `--report tmp_report.md`, `output_clean.md`, and both inputs.
- Assert the file `tmp_report.md` exists.
- Assert it contains `"Status: CLEAN"`.
- Clean up the file after the test.

**test_cli_stage_flag**
Invoke with `--stage 02_draft`, `output_draft.md`, and both inputs.
- Assert stdout contains `"Stage: 02_draft"`.

**test_cli_threshold_flag**
Invoke with `--threshold 0.9`, `output_draft.md`, and both inputs.
- High threshold should force all passages below floor.
- Assert `returncode == 1` (DRIFT).
- Assert stdout contains `"Unattributed passages: 3"` (or the total passage count).

**test_cli_semantic_flag_imports**
Invoke with `--semantic`, `output_draft.md`, and both inputs.
- If `sentence-transformers` is installed, assert `returncode` is either 0 or 1
  (no crash).
- If not installed, assert the process exits non-zero with an error message
  mentioning `sentence-transformers`.

**test_cli_no_inputs_error**
Invoke without `--inputs`.
- Assert `returncode != 0`.
- Assert stderr or stdout contains an error about missing inputs.

**Verification:**
```
pytest tests/test_cli.py -x
```

Then run:
```
pytest -x
```
All Phase 1–4 tests must pass.

---

## Step 4.5 — `pytest -x` (full suite)

**Action:** Run the entire test suite.

**Verification:**
```
pytest -x
```
All tests must pass. If any fail, fix before proceeding.

---

## Step 4.6 — Manual CLI smoke test

**Action:** Run the CLI manually on the CLEAN fixture set.

**Verification:**
```
python sem_debug.py tests/fixtures/output_clean.md --inputs tests/fixtures/input_source_alpha.md tests/fixtures/input_source_beta.md --stage 02_draft
```

Expect:
- Exit code `0`.
- Stdout contains `Status: CLEAN`.
- Stdout contains `Verdict`.
- Stdout contains `Stage: 02_draft`.
- No exceptions, no tracebacks.

Then run the DRIFT case:
```
python sem_debug.py tests/fixtures/output_draft.md --inputs tests/fixtures/input_source_alpha.md tests/fixtures/input_source_beta.md
```

Expect:
- Exit code `1`.
- Stdout contains `Status: DRIFT`.

Then run the BLOCKED case:
```
python sem_debug.py tests/fixtures/output_draft.md --inputs tests/fixtures/input_source_alpha.md tests/fixtures/input_source_beta.md --strict
```

Expect:
- Exit code `2`.
- Stdout contains `Status: BLOCKED`.

---

## Phase 4 Risks (from Phase 3 vetting — monitor during build)

| ID | Risk | Mitigation in this plan |
|---|---|---|
| R-3 | Absolute paths in `source_file` if CLI receives absolute paths | CLI must pass paths exactly as received (Step 4.3, item 8). `parser.py` will store whatever string is passed. Test with relative paths only; absolute path behavior is out of scope for MVP. |
| R-4 | Missing `requirements.txt` | Step 4.0 creates it. Step 4.2 creates `requirements-semantic.txt`. Both must exist at exit gate. |

---

## Phase 4 Exit Gate

Phase 4 is complete when:

1. `pytest -x` passes with zero failures across all test files.
2. `python sem_debug.py --help` exits clean.
3. Manual smoke tests (CLEAN, DRIFT, BLOCKED) produce correct exit codes and output.
4. `requirements.txt` exists with `scikit-learn`.
5. `requirements-semantic.txt` exists with `sentence-transformers` and `torch`.
6. No modifications were made to `parser.py`.
7. `matcher.py` modification is limited to the semantic extension only.

Report pass count and any failures to the PM before declaring Phase 4 complete.

---

*Read first. Verify second. Ship last.*
