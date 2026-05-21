# PHASE3_NS.md — Build Plan Phase 3
# Tracer and Reporter

Source of truth for Phase 3. CODE reads this before touching any file.
Run `pytest -x` after every step. Do not proceed to the next step if any test fails.

---

## Carry-Forward Decisions

These are settled. Do not re-decide them.

- `parse_file(path: str) -> list[Passage]` is the parser contract.
- `match_passages` returns `tuple[list[Match], list[tuple[Passage, float]]]`.
  The float in the second list is the best-failed TF-IDF score for that passage.
  Unattributed passages that had no comparisons (empty corpus) carry 0.0.
- `semantic: bool = False` is accepted by `match_passages` and ignored in Phase 3.
  tracer.py passes the flag through. No semantic logic in tracer.py.
- Verdict at the library layer is `CLEAN` or `DRIFT` only.
  `BLOCKED` and `--strict` promotion live in the CLI (Phase 4).
- `source_file` on every Passage is a relative path from workspace root.
  tracer.py must pass paths to `parse_file` exactly as received — do not resolve
  to absolute paths before calling parse_file.
- Line numbers are 1-based.
- No `__init__.py` anywhere. `conftest.py` handles sys.path.
- Typed exceptions only. Never bare `Exception`.
- No network calls in any test. All fixtures are disk-based static files.
- All fixtures live in `tests/fixtures/`.

Architectural decisions governing Phase 3: AD-01, AD-03, AD-07, AD-08,
AD-09, AD-11, AD-12, AD-13. Read ARCHITECT_DEC.md if any decision below
is unclear.

---

## Models Reference

These are the models CODE will use. Do not modify models.py in Phase 3.

```python
@dataclass
class Passage:
    text: str
    source_file: str
    line_start: int
    line_end: int

@dataclass
class Match:
    output_passage: Passage
    input_passage: Passage
    score: float        # 0.0–1.0, rounded to 4 decimal places
    method: str         # "tfidf" or "semantic"

@dataclass
class TraceResult:
    stage: str
    output_file: str
    input_files: list[str]
    matches: list[Match]
    unattributed: list[tuple[Passage, float]]

@dataclass
class Verdict:
    status: str         # "CLEAN" or "DRIFT"
    exit_code: int      # 0 = CLEAN, 1 = DRIFT

DEFAULT_THRESHOLD = 0.35
```

If TraceResult or Verdict are not yet in models.py, add them now as the
first action before Step 3.0. Run `pytest -x` to confirm no regressions.

---

## Report Format Reference

reporter.py must produce output matching this structure exactly.
This is the contract test_reporter.py asserts against.

```
# sem_debug Trace Report

Stage: 02_draft
Output: tests/fixtures/output_draft.md
Inputs: tests/fixtures/input_source_alpha.md, tests/fixtures/input_source_beta.md

---

## Attributed Passages

### Passage (lines 1–4)
> Models are increasingly deployed in quantized form to reduce memory
> footprint and inference latency.

Source: tests/fixtures/input_source_alpha.md (lines 3–6)
Score: 0.8421 | Method: tfidf

---

## Unattributed Passages

### Passage (lines 9–12)
> Orcas in the Pacific Northwest have demonstrated coordinated hunting
> strategies across multigenerational pods.

Best score: 0.0312 | No source in declared inputs.

---

## Verdict

Status: DRIFT
Unattributed passages: 1
Exit code: 1
```

Rules:
- Header is exactly `# sem_debug Trace Report`.
- Attributed section header is exactly `## Attributed Passages`.
- Unattributed section header is exactly `## Unattributed Passages`.
- Verdict section header is exactly `## Verdict`.
- Passage text is quoted with `> ` prefix on every line.
- Line ranges are 1-based, format `lines N–M` (en dash, not hyphen).
- Score is formatted to 4 decimal places.
- Best score for unattributed passages comes from the float in
  `tuple[Passage, float]` — reporter does not recompute it.
- If unattributed is empty, omit the `## Unattributed Passages` section entirely.
- If matches is empty, omit the `## Attributed Passages` section entirely.
- Verdict block always present regardless of status.

---

## Step 3.0 — `tests/fixtures/output_clean.md`

Action: Create a fixture where every paragraph is closely paraphrased from
`input_source_alpha.md` or `input_source_beta.md`. All passages must score
above DEFAULT_THRESHOLD (0.35) on TF-IDF alone. Minimum 2 paragraphs.
Do not copy text verbatim — paraphrase so TF-IDF succeeds on vocabulary
overlap, not exact string match. This fixture is required by test_tracer.py
for the CLEAN case. It must exist before any tracer tests are written.

Verification:
```
python -c "
import pathlib
p = pathlib.Path('tests/fixtures/output_clean.md')
assert p.exists()
assert len(p.read_text().strip().split('\n\n')) >= 2
print('OK')
"
```

Then run:
```
pytest -x
```
All 18 existing tests must still pass before proceeding.

---

## Step 3.1 — `tracer.py`

Action: Create `tracer.py` in the workspace root exposing one public function:

```python
def trace(
    output_file: str,
    input_files: list[str],
    stage: str = "",
    threshold: float = DEFAULT_THRESHOLD,
    semantic: bool = False,
) -> tuple[TraceResult, Verdict]:
```

Implementation requirements:

1. Call `parse_file(output_file)` to get output passages.
2. For each path in `input_files`, call `parse_file(path)` and concatenate
   results into a flat list of input passages.
3. Call `match_passages(output_passages, input_passages, threshold, semantic)`.
4. Assemble a `TraceResult`:
   - `stage` = the stage parameter as received
   - `output_file` = the output_file parameter as received
   - `input_files` = the input_files list as received
   - `matches` = first element of match_passages return tuple
   - `unattributed` = second element of match_passages return tuple
5. Compute Verdict:
   - `CLEAN` (exit_code=0) if `len(trace_result.unattributed) == 0`
   - `DRIFT` (exit_code=1) if `len(trace_result.unattributed) > 0`
6. Return `(trace_result, verdict)`.

Do not resolve paths to absolute. Do not modify paths before passing to
parse_file. Do not implement any semantic logic — pass the flag through only.

Verification:
```
python -c "from tracer import trace; print('OK')"
```

Then run:
```
pytest -x
```
All 18 existing tests must still pass.

---

## Step 3.2 — `tests/test_tracer.py`

Action: Create `tests/test_tracer.py`. Import `tracer`, `models`.
Use `parse_file` only if needed to inspect fixture content for setup.
Do not import matcher directly — test tracer through its public interface only.

Write the following tests. Each test calls `trace` and asserts on the
returned `(TraceResult, Verdict)` tuple.

**test_drift_case**
Call `trace` with `output_draft.md` and both input sources.
- `result.stage` is empty string (no stage passed).
- `result.output_file` == `"tests/fixtures/output_draft.md"`.
- `result.input_files` == the list passed in, order preserved.
- `len(result.matches) >= 1`.
- `len(result.unattributed) >= 1`.
- Every match has `method == "tfidf"`.
- Every match has `0.0 <= score <= 1.0`.
- `verdict.status == "DRIFT"`.
- `verdict.exit_code == 1`.

**test_clean_case**
Call `trace` with `output_clean.md` and both input sources.
- `len(result.unattributed) == 0`.
- `len(result.matches) >= 1`.
- `verdict.status == "CLEAN"`.
- `verdict.exit_code == 0`.

**test_stage_field_populated**
Call `trace` with `stage="02_draft"`, `output_draft.md`, both input sources.
- `result.stage == "02_draft"`.

**test_unattributed_carries_best_score**
Call `trace` with `output_draft.md` and both input sources.
- For every `(passage, score)` in `result.unattributed`:
  assert `isinstance(score, float)`.
  assert `0.0 <= score < DEFAULT_THRESHOLD`.

**test_empty_inputs**
Call `trace` with `output_draft.md` and an empty input_files list.
- `len(result.matches) == 0`.
- `len(result.unattributed) > 0`.
- Every unattributed tuple has score `0.0`.
- `verdict.status == "DRIFT"`.

**test_source_file_paths_preserved**
Call `trace` with `output_draft.md` and `["tests/fixtures/input_source_alpha.md"]`.
- Every match's `input_passage.source_file` starts with
  `"tests/fixtures/input_source_alpha.md"`.
- `result.input_files[0] == "tests/fixtures/input_source_alpha.md"`.

Verification:
```
pytest tests/test_tracer.py -x
```

Then run:
```
pytest -x
```
All tests (18 existing + new tracer tests) must pass.

---

## Step 3.3 — `reporter.py`

Action: Create `reporter.py` in the workspace root exposing one public function:

```python
def render(trace_result: TraceResult, verdict: Verdict) -> str:
```

Returns a plain markdown string. No terminal escape codes. No color.
No external dependencies beyond the standard library.

Implementation requirements — follow the Report Format Reference above exactly:

1. Header block: `# sem_debug Trace Report`, blank line, then Stage / Output /
   Inputs lines. Stage line omitted if `trace_result.stage` is empty string.
   Inputs line is a comma-separated list of all paths in `trace_result.input_files`.

2. Attributed section: present only if `len(trace_result.matches) > 0`.
   For each Match:
   - Subheader: `### Passage (lines N–M)` using output_passage line numbers.
     Use en dash (–) not hyphen (-).
   - Quoted text: every line of `output_passage.text` prefixed with `> `.
   - Source line: `Source: {input_passage.source_file} (lines N–M)`
   - Score line: `Score: {score:.4f} | Method: {method}`
   - Separator: `---` between passages, not after the last one.

3. Unattributed section: present only if `len(trace_result.unattributed) > 0`.
   For each `(passage, best_score)` tuple:
   - Subheader: `### Passage (lines N–M)` using passage line numbers.
   - Quoted text: every line of `passage.text` prefixed with `> `.
   - Score line: `Best score: {best_score:.4f} | No source in declared inputs.`
   - Separator: `---` between passages, not after the last one.

4. Verdict block: always present.
   ```
   ## Verdict

   Status: {status}
   Unattributed passages: {count}
   Exit code: {exit_code}
   ```

Verification:
```
python -c "from reporter import render; print('OK')"
```

Then run:
```
pytest -x
```
All tests must still pass.

---

## Step 3.4 — `tests/test_reporter.py`

Action: Create `tests/test_reporter.py`. Import `models` and `reporter`.
Build all TraceResult and Verdict objects programmatically — do not call
parse_file or trace. This isolates reporter tests from parser and tracer.

Construct a minimal fixture set at the top of the file:

```python
PASSAGE_OUT_1 = Passage(
    text="Models are increasingly deployed in quantized form.",
    source_file="tests/fixtures/output_draft.md",
    line_start=1,
    line_end=2,
)
PASSAGE_IN_1 = Passage(
    text="Post-training quantization reduces memory and latency.",
    source_file="tests/fixtures/input_source_alpha.md",
    line_start=3,
    line_end=4,
)
PASSAGE_OUT_2 = Passage(
    text="Orcas in the Pacific Northwest hunt in coordinated pods.",
    source_file="tests/fixtures/output_draft.md",
    line_start=5,
    line_end=6,
)
MATCH_1 = Match(
    output_passage=PASSAGE_OUT_1,
    input_passage=PASSAGE_IN_1,
    score=0.8421,
    method="tfidf",
)
```

Write the following tests:

**test_report_header_present**
Build a TraceResult with one match, zero unattributed, stage="02_draft".
Call render. Assert `"# sem_debug Trace Report"` in output.

**test_stage_line_present**
Same TraceResult. Assert `"Stage: 02_draft"` in output.

**test_stage_line_absent_when_empty**
Build a TraceResult with stage="". Assert `"Stage:"` not in output.

**test_output_line_present**
Assert `"Output: tests/fixtures/output_draft.md"` in output.

**test_inputs_line_present**
Assert `"Inputs:"` in output and the input source filename appears in the line.

**test_attributed_section_present**
Assert `"## Attributed Passages"` in output.

**test_attributed_passage_text_quoted**
Assert every line of PASSAGE_OUT_1.text appears in output prefixed with `"> "`.

**test_attributed_source_line**
Assert `"Source: tests/fixtures/input_source_alpha.md (lines 3–4)"` in output.
En dash, not hyphen.

**test_attributed_score_line**
Assert `"Score: 0.8421 | Method: tfidf"` in output.

**test_unattributed_section_present**
Build a TraceResult with zero matches and one unattributed:
`[(PASSAGE_OUT_2, 0.0312)]`. Verdict DRIFT.
Assert `"## Unattributed Passages"` in output.

**test_unattributed_passage_text_quoted**
Same TraceResult. Assert every line of PASSAGE_OUT_2.text appears prefixed with `"> "`.

**test_unattributed_score_line**
Assert `"Best score: 0.0312 | No source in declared inputs."` in output.

**test_unattributed_section_absent_when_clean**
Build a TraceResult with one match, zero unattributed. Verdict CLEAN.
Assert `"## Unattributed Passages"` not in output.

**test_attributed_section_absent_when_all_unattributed**
Build a TraceResult with zero matches, one unattributed. Verdict DRIFT.
Assert `"## Attributed Passages"` not in output.

**test_verdict_block_present**
Assert `"## Verdict"` in output.

**test_verdict_status_drift**
TraceResult with one unattributed. Assert `"Status: DRIFT"` in output.

**test_verdict_status_clean**
TraceResult with zero unattributed. Assert `"Status: CLEAN"` in output.

**test_verdict_exit_code**
Assert `"Exit code: 1"` in output for DRIFT case.
Assert `"Exit code: 0"` in output for CLEAN case.

**test_verdict_unattributed_count**
Assert `"Unattributed passages: 1"` in output for one unattributed passage.
Assert `"Unattributed passages: 0"` in output for zero unattributed passages.

Verification:
```
pytest tests/test_reporter.py -x
```

Then run:
```
pytest -x
```
All Phase 1, 2, and 3 tests must pass.

---

## Phase 3 Exit Gate

Phase 3 is complete when:

1. `pytest -x` passes with zero failures across all test files.
2. `python -c "from tracer import trace; print('OK')"` exits clean.
3. `python -c "from reporter import render; print('OK')"` exits clean.
4. `tests/fixtures/output_clean.md` exists with at least 2 paragraphs.
5. No modifications were made to `matcher.py`, `parser.py`, or `models.py`
   beyond adding `TraceResult` and `Verdict` if they were absent.

Do not begin Phase 4 until all five conditions are met.
Report pass count and any failures to the PM before proceeding.