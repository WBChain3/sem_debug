# NORTHSTAR2.md — Build Plan Phases 2–4

## Carry-Forward Decisions from Phase 1 / NORTHSTAR

- `parse_file(path: str) -> list[Passage]` is the parser contract.
- All fixtures are disk-based static files in `tests/fixtures/`.
- No network calls in any test.
- Typed exceptions only — never bare `Exception`.
- `conftest.py` handles `sys.path` insert; no `__init__.py`.
- Line numbering is 1-based; `source_file` is a relative path from workspace root.
- Code blocks are silently skipped by the parser.
- Headers merge with the following paragraph; never standalone passages.

---

## Phase 2 Steps — TF-IDF Matcher

### Step 2.0 — `parser.py`
Action: Move the `import pathlib` statement from inside `parse_file` to the top-level imports at the start of the file.
Verification: `python -m pytest tests/test_parser.py -x` (must still pass after refactor).

### Step 2.1 — `tests/fixtures/input_source_alpha.md`
Action: Create a realistic input source fixture with 2–3 prose paragraphs on a technical topic (e.g., research findings).
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/input_source_alpha.md'); assert p.exists() and len(p.read_text().strip().split('\n\n')) >= 2; print('OK')"`

### Step 2.2 — `tests/fixtures/input_source_beta.md`
Action: Create a second realistic input source fixture with distinct content (e.g., a design spec) so the two inputs share no vocabulary.
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/input_source_beta.md'); assert p.exists() and p.read_text().strip(); print('OK')"`

### Step 2.3 — `tests/fixtures/output_draft.md`
Action: Create an output fixture that closely paraphrases one paragraph from `input_source_alpha.md` and one from `input_source_beta.md`, and adds one clearly novel paragraph unrelated to both inputs.
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/output_draft.md'); assert p.exists() and len(p.read_text().strip().split('\n\n')) >= 3; print('OK')"`

### Step 2.4 — `tests/fixtures/output_unrelated.md`
Action: Create an output fixture whose content is entirely unrelated to both `input_source_alpha.md` and `input_source_beta.md` (e.g., a recipe or sports summary).
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/output_unrelated.md'); assert p.exists() and p.read_text().strip(); print('OK')"`

### Step 2.5 — `matcher.py`
Action: Create `matcher.py` exposing `match_passages(output_passages: list[Passage], input_passages: list[Passage], threshold: float, semantic: bool = False) -> tuple[list[Match], list[Passage]]`. It must use `sklearn.feature_extraction.text.TfidfVectorizer` to vectorize input passages, score each output passage via cosine similarity against all input passages, and return a tuple where the first element is a list of `Match` objects (method="tfidf", score in 0.0–1.0) and the second is the list of unattributed `Passage` objects (score < threshold). The `semantic` parameter is accepted for forward compatibility but ignored in Phase 2.
Verification: `python -c "from matcher import match_passages; print('OK')"`

### Step 2.6 — `tests/test_matcher.py`
Action: Create `tests/test_matcher.py` importing `models` and `matcher`. Write tests that: parse fixtures into passages; assert known-related output passages from `output_draft.md` match input passages above threshold with `method="tfidf"`; assert `output_unrelated.md` passages fall below threshold and are returned as unattributed; assert empty input corpus yields all passages unattributed; assert all `Match.score` values are in `[0.0, 1.0]`.
Verification: `pytest tests/test_matcher.py -x`

### Step 2.7 — `tests/test_matcher_calibration.py`
Action: Create a calibration test that parses the full realistic fixture corpus (`input_source_alpha.md`, `input_source_beta.md`, `output_draft.md`, `output_unrelated.md`), runs `match_passages` with `DEFAULT_THRESHOLD`, and asserts that (a) known-related output passages score >= threshold and are attributed, and (b) known-unrelated passages score < threshold and are unattributed. If this fails, revise `DEFAULT_THRESHOLD` in `models.py`.
Verification: `pytest tests/test_matcher_calibration.py -x`

### Step 2.8 — `requirements.txt`
Action: Create `requirements.txt` listing `scikit-learn` as the only required dependency.
Verification: `python -c "import pathlib; p = pathlib.Path('requirements.txt'); assert 'scikit-learn' in p.read_text(); print('OK')"`

---

## Phase 3 Steps — Tracer and Reporter

### Step 3.1 — `tracer.py`
Action: Create `tracer.py` exposing `trace(output_file: str, input_files: list[str], stage: str = "", threshold: float = DEFAULT_THRESHOLD, semantic: bool = False) -> tuple[TraceResult, Verdict]`. It must call `parse_file` on all paths, call `match_passages` with the parsed passages and threshold, assemble a `TraceResult` (populating `stage`, `output_file`, `input_files`, `matches`, `unattributed`), compute the `Verdict` (`CLEAN` if `unattributed` is empty; `DRIFT` otherwise), and return both objects.
Verification: `python -c "from tracer import trace; print('OK')"`

### Step 3.2 — `tests/test_tracer.py`
Action: Create `tests/test_tracer.py` importing `tracer`, `parser`, and `models`. Write tests that call `trace` with fixture paths and assert: the returned `TraceResult` has the correct `stage` and `input_files`; `matches` contain the expected `method="tfidf"`; `unattributed` contains the expected novel paragraph from `output_draft.md`; `Verdict.status` is `"CLEAN"` for the `output_clean.md` case (after Phase 4) or `"DRIFT"` for the `output_draft.md` case; `Verdict.exit_code` matches status.
Verification: `pytest tests/test_tracer.py -x`

### Step 3.3 — `reporter.py`
Action: Create `reporter.py` exposing `render(trace_result: TraceResult, verdict: Verdict) -> str` that returns a markdown string matching the report format in PLAN.md (attributed passages, unattributed passages, verdict summary, quoted text, scores with methods). No terminal styling — plain markdown only.
Verification: `python -c "from reporter import render; print('OK')"`

### Step 3.4 — `tests/test_reporter.py`
Action: Create `tests/test_reporter.py` importing `models` and `reporter`. Build a `TraceResult` and `Verdict` programmatically (no parser needed), call `render`, and assert: output contains `# sem_debug Trace Report`; attributed section shows passage text, source file, line range, score, and method; unattributed section shows passage text and explanatory message; final verdict block shows status, count, and exit code.
Verification: `pytest tests/test_reporter.py -x`

---

## Phase 4 Steps — CLI and Integration

### Step 4.1 — `tests/fixtures/output_clean.md`
Action: Create an output fixture where every paragraph is closely paraphrased from `input_source_alpha.md` or `input_source_beta.md` so that TF-IDF attribution succeeds for all passages (zero unattributed).
Verification: `python -c "import pathlib; p = pathlib.Path('tests/fixtures/output_clean.md'); assert p.exists() and len(p.read_text().strip().split('\n\n')) >= 2; print('OK')"`

### Step 4.2 — `matcher.py` (semantic extension)
Action: Edit `matcher.py` so that when `semantic=True`, after TF-IDF scoring, any unattributed passage is re-encoded with `sentence-transformers` and rescored. Requires graceful fallback: if `sentence-transformers` is not installed, raise a typed exception with a clear user-facing message. If the semantic score >= threshold, upgrade the match to attributed with `method="semantic"`. Passages failing both methods remain unattributed.
Verification: `python -c "from matcher import match_passages; print('OK')"`

### Step 4.3 — `requirements-semantic.txt`
Action: Create `requirements-semantic.txt` listing `sentence-transformers` and `torch`.
Verification: `python -c "import pathlib; t = pathlib.Path('requirements-semantic.txt').read_text(); assert 'sentence-transformers' in t and 'torch' in t; print('OK')"`

### Step 4.4 — `sem_debug.py`
Action: Create `sem_debug.py` as the CLI entry point. Argument parsing must support: `sem_debug <output_file> --inputs <file1> [file2 ...]`; optional flags `--stage`, `--threshold`, `--semantic`, `--report`, `--strict`. Call `tracer.trace()` and `reporter.render()`, print the markdown report to stdout or to `--report FILE`, and exit with `Verdict.exit_code`.
Verification: `python sem_debug.py --help` completes without error.

### Step 4.5 — `tests/test_cli.py`
Action: Create `tests/test_cli.py` using `subprocess.run` to invoke `python sem_debug.py` with fixture paths. Tests must cover: CLEAN case (`output_clean.md` yields exit 0); DRIFT case (`output_draft.md` yields exit 1); BLOCKED case (pass `--strict` with `output_draft.md` to force exit 2); `--json` pipeable output if implemented, otherwise verify markdown output to stdout. No live API calls.
Verification: `pytest tests/test_cli.py -x`

### Step 4.6 — `pytest -x` (full suite)
Action: Run the entire test suite (`pytest -x`) and confirm all Phase 1–4 tests pass without modification.
Verification: `pytest -x`

### Step 4.7 — Manual CLI smoke test
Action: Run the CLI manually on the CLEAN fixture set and verify exit code 0 and markdown report printed to stdout.
Verification: `python sem_debug.py tests/fixtures/output_clean.md --inputs tests/fixtures/input_source_alpha.md tests/fixtures/input_source_beta.md --stage 02_draft` (exit code 0, output contains `Verdict: CLEAN`).

---

## Flagged Ambiguities

1. **Calibration fixture design (Step 2.7).** PLAN.md says threshold default is `0.35` and is provisional, but provides no corpus size, expected TF-IDF score distribution, or guidance on how much paraphrase is realistic. CODE must decide how closely `output_draft.md` should paraphrase the inputs to calibrate the floor.

2. **`--json` flag.** CLI Interface lists `--json` implicitly ("valid and pipeable" in RESEARCH.md Phase 2 checklist), but PLAN.md's CLI options table does **not** include `--json`. CODE must decide whether `--json` is in or out of MVP.

3. **`BLOCKED` semantics in Phase 3.** PLAN.md says `BLOCKED` means "unattributed passages exceed threshold or `--strict` fired." The phrase "exceed threshold" is undefined — is it a count threshold, a ratio threshold, or simply `--strict`? CODE must choose the logic for `BLOCKED` independent of `--strict`.

4. **`Match` object for unattributed passages.** In Phase 2, `match_passages` returns `(matches, unattributed)`. But the report example shows a "best: 0.21" score for unattributed passages. CODE must decide whether `match_passages` also returns best-failed scores so the reporter can render them, or whether the reporter computes them separately.

5. **`--strict` + semantic fallback interaction.** If `--strict` is set and `--semantic` is also set, should semantic-matched passages count as attributed and therefore prevent `--strict` from firing? CODE must decide the flag precedence.

6. **`semantic` parameter in `tracer.trace`.** PLAN.md says semantic "runs after TF-IDF on failures only," but the `tracer.py` signature could either delegate this entirely to `matcher.py` or implement the second-pass logic itself. CODE must choose where the semantic branch lives.

7. **Fixture re-use across phases.** Step 4.1 introduces `output_clean.md`, but `test_tracer.py` (Step 3.2) references it before it is created. CODE must decide whether to defer those assertions or create a placeholder earlier.

8. **`Match.output_passage` vs. `Passage` identity.** In the report example, quoted passages show original text. If `parse_file` strips or normalizes text, the `Passage.text` in `Match` may differ from what a human reading the markdown file sees. CODE must decide whether `Passage.text` is raw or normalized.

9. **`source_file` in `Match.input_passage` for multi-input runs.** When multiple input files are passed, each parsed passage carries its own `source_file`. The report shows relative paths. CODE must ensure `tracer.trace` passes the exact paths to `parse_file` so that `source_file` matches the `Inputs:` line in the report.

10. **Exit code 2 from `--strict` without an explicit count/ratio threshold.** If `--strict` is the *only* path to `BLOCKED`, the CLI's `--strict` flag effectively overrides the default DRIFT logic. This is acceptable if documented, but the plan is ambiguous on whether `BLOCKED` can occur naturally.
