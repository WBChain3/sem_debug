# ARCHITECT_DEC.md — sem_debug Architectural Decisions

Append-only. Each entry records what was decided, why, and what it closes.

---

## Session 1 — Phase 1 Complete

### AD-01 — Attribution method: post-hoc matching
**Decision:** sem_debug attributes output passages to input files via post-hoc
similarity matching. The agent does not annotate its own output at generation time.
**Reason:** Agent-annotated provenance inherits agent hallucination risk. If the agent
is confused about where it is in the decision tree, its annotations are wrong.
Post-hoc matching reads what actually exists on disk — no agent opinion involved.
**Closes:** Core architecture question from Van Clief §6.2.

---

### AD-02 — Two-pass matching: TF-IDF default, semantic opt-in
**Decision:** Default matcher is TF-IDF via scikit-learn. Semantic matching via
sentence-transformers (`all-MiniLM-L6-v2`) is available via `--semantic` flag.
Semantic pass runs only on passages that fail TF-IDF threshold — not on the full corpus.
**Reason:** Tool must be lightweight enough that people actually use it. Heavy means
people won't consider it. TF-IDF works out of the box on any ICM workspace with no
model download. Semantic is available when you need it without penalising the default path.
**Closes:** Dependency and portability question.

---

### AD-03 — Exit codes as typed verdicts
**Decision:** sem_debug exits with typed codes: 0 (CLEAN), 1 (DRIFT), 2 (BLOCKED).
`--strict` flag promotes any unattributed passage to BLOCKED.
**Reason:** Enables gate integration in any pipeline or shell script without parsing
output. Fits the phase-gate pattern from the operator's existing workflow.
**Closes:** Pipeline integration design.

---

### AD-04 — Chunking: blank-line-delimited paragraphs
**Decision:** parser.py splits markdown into passages at blank lines.
Sentence-level chunking was rejected. Sliding windows were rejected.
**Reason:** Sentence-level is too granular for TF-IDF to produce meaningful term
frequency at this corpus size. Sliding windows add complexity with no MVP benefit.
Paragraph-level matches how humans reason about attribution.
**Closes:** PLAN.md ambiguity item 3.

---

### AD-05 — Headers merge with following paragraph
**Decision:** Markdown headers are not standalone passages. A header merges with
the prose paragraph that follows it. A header with no following paragraph is discarded.
`header_only.md` returns `[]`.
**Reason:** A header without its body is not meaningfully attributable to any input.
Standalone header passages would produce noise in the trace report.
**Closes:** PLAN.md ambiguity item 4.

---

### AD-06 — Code blocks skipped silently
**Decision:** Fenced code blocks are skipped by the parser and produce no Passage
objects. They are not flagged in the trace report.
**Reason:** Constraints section overrules the Phase 1 parenthetical "(skip or flag)".
Code block content is implementation detail, not semantic content to be attributed.
**Closes:** PLAN.md ambiguity item 2.

---

### AD-07 — source_file stores relative path from workspace root
**Decision:** `Passage.source_file` stores the path relative to the workspace root,
not an absolute path or basename.
**Reason:** Keeps traces portable across machines. Matches the report format example
in PLAN.md. Absolute paths break when workspaces are copied or synced.
**Closes:** PLAN.md ambiguity item 6.

---

### AD-08 — Line numbers are 1-based
**Decision:** `Passage.line_start` and `line_end` are 1-based integers.
**Reason:** Matches how humans read files and how editors report line numbers.
Matches the report format example (lines 12–16) in PLAN.md.
**Closes:** PLAN.md ambiguity item 7.

---

### AD-09 — tests/ packaging via conftest.py, no __init__.py
**Decision:** `tests/conftest.py` inserts the workspace root into `sys.path`.
No `__init__.py` files anywhere in the project.
**Reason:** Flat and simple. Keeps the project portable without packaging overhead.
Consistent with a standalone CLI tool that does not need to be installed as a package.
**Closes:** PLAN.md ambiguity item 8.

---

### AD-10 — DEFAULT_THRESHOLD validated at 0.35
**Decision:** DEFAULT_THRESHOLD = 0.35 confirmed as correct default.
**Reason:** Calibration pass in Phase 2 (test_matcher_calibration.py) validated
all three zones against real fixture content:
- Zone 1 (high lexical overlap): Match above 0.35 — TF-IDF attributes correctly
- Zone 2 (paraphrase): None — TF-IDF correctly rejects, semantic pass rescues in Phase 4
- Zone 3 (unrelated): None — correctly unattributed on both axes
Fixture rewrite required: input_source_beta.md and Zone 2 of output_draft.md were
rewritten to achieve genuine vocabulary disjointness. Original beta fixture scored
0.643 — too lexically similar to demonstrate two-pass design. Final Zone 2 score
confirmed below 0.35.
**Closes:** AD-10 open item. Threshold ships as validated default.

---

### AD-11 — HTML comments skipped silently by parser
**Decision:** Lines starting with `<!--` produce no Passage objects.
Same mechanism as fenced code blocks.
**Reason:** HTML comment zone markers in output_draft.md are fixture scaffolding,
not semantic content. Emitting them as Passages would pollute matcher input with
non-attributable content and add noise to calibration tests.
**Closes:** Parser edge case surfaced during Phase 2 fixture design.

---

AD-12 — Unattributed passages carry best-failed score as tuple, not model field
Decision: match_passages returns tuple[list[Match], list[tuple[Passage, float]]]. The float is the highest TF-IDF score the passage achieved against any input passage in that run, even though it did not clear the threshold. The score is not stored on the Passage model.
Reason: Attaching best_score to Passage (Option A) would conflate parse artifacts with matcher output. If matching becomes multi-pass or learned — reranking layer, CNN scorer, fine-tuned cross-encoder — a single float on Passage becomes ambiguous: which pass produced it, against which corpus, with which model version. Keeping the score in the return tuple means it exists only in the context of the matching event that produced it. The model layer stays clean regardless of how the matching pipeline evolves.
Closes: MI-2 from Phase 2 vetting report. Option A/B decision from session 2.

---

AD-13 — Empty-input early returns yield zero-score tuples, not None sentinels
Decision: When match_passages is called with an empty input corpus or empty output list, the second return element is [(p, 0.0) for p in output_passages], not [None] * len(output_passages).
Reason: Under the new return type, None sentinels are structurally illegal. A 0.0 float is semantically correct — no comparison was made, so the best-failed score is zero by definition. All downstream consumers receive a consistent type regardless of whether the corpus was empty or matching simply failed.
Closes: Edge case surfaced during CB-1 fix, session 2.

---

## Phase 1 Status: COMPLETE
6/6 tests passing. No drift. No blockers.

## Phase 2 Status: COMPLETE
Steps 2.0–2.8 done. All tests passing.
- matcher.py: match_passages() with TF-IDF, scikit-learn, typed exceptions
- Calibration validated: DEFAULT_THRESHOLD = 0.35 confirmed
- Two fixes from RESEARCH vet: dead pathlib import removed, ValueError documented
- One contract violation: RESEARCH wrote fixture files (steps 2.1–2.4) instead
  of specifying inline. Files were correct and kept. Violation logged.

---

## Session 2 — Phase 3 Complete

### AD-14 — TraceResult and Verdict signatures aligned to matcher contract
**Decision:** `TraceResult.unattributed` changed from `list[Passage]` to `list[tuple[Passage, float]]`. `Verdict.summary` field removed entirely.
**Reason:** `matcher.py` already returned `list[tuple[Passage, float]]` per AD-12, but `models.py` still declared `list[Passage]`. This created a structural mismatch that blocked `tracer.py` from assembling a `TraceResult` without violating its own type annotation. `summary` was removed because the Phase 3 spec for `Verdict` only defines `status` and `exit_code`; no downstream consumer used it, and it forced `tracer.py` to invent a string value not present in the plan.
**Closes:** CB-1 and CB-2 from pre-Phase 3 vetting report.

---

### AD-15 — BLOCKED is a CLI-only verdict promotion
**Decision:** `tracer.py` computes only `CLEAN` (exit 0) and `DRIFT` (exit 1). `BLOCKED` (exit 2) is computed by `sem_debug.py` when `--strict` is present. There is no natural count/ratio threshold for `BLOCKED` independent of `--strict`.
**Reason:** Library layer should be simple and deterministic. Policy decisions like `--strict` belong at the CLI boundary where user intent is parsed. Keeping `BLOCKED` out of `tracer.py` preserves the separation between analysis (what the text says) and policy (what the pipeline should do about it).
**Closes:** NORTHSTAR2.md ambiguity #3 and #10.

---

### AD-16 — JSON output deferred out of MVP
**Decision:** The `--json` flag is not implemented in Phase 4. CLI outputs markdown only.
**Reason:** `PHASE3_NS.md` specifies a single markdown report format with exact headers, separators, and en-dash rules. Adding JSON would require a parallel formatter, schema maintenance, and additional test surface with no established user demand. If needed later, it is a feature addition, not a plan gap.
**Closes:** NORTHSTAR2.md ambiguity #2.

---

### AD-17 — Semantic second-pass stays inside matcher.py
**Decision:** When `semantic=True`, the TF-IDF → semantic fallback chain is entirely inside `match_passages`. `tracer.trace` passes the flag through but never branches on it.
**Reason:** Centralizes matching logic in one module. `tracer.py` remains a thin orchestrator. Prevents semantic-specific code (model loading, encoding, cosine similarity) from leaking into the orchestration layer. Matches the design principle that `tracer` wires modules; `matcher` implements matching.
**Closes:** NORTHSTAR2.md ambiguity #6.

---

### AD-18 — source_file relative path enforced by caller convention
**Decision:** `parser.py` stores `str(filepath)` exactly as received. The relative-path contract (AD-07) is upheld by CLI and tests passing relative paths only. `parser.py` does not normalize or rewrite user-provided paths.
**Reason:** A low-level file reader should not silently change the strings it receives. Path policy belongs at the entry point (`sem_debug.py`), which must not resolve to absolute before calling `tracer.trace`. Real-world absolute-path usage is out of scope for MVP; the contract is documented and tested with relative paths.
**Closes:** R-3 from Phase 3 vetting report.

---

## Phase 3 Status: COMPLETE
Steps 3.0–3.4 done. 43/43 tests passing.
- output_clean.md: 2 paragraphs, all TF-IDF scores > 0.35
- tracer.py: trace() with stage, threshold, semantic passthrough
- reporter.py: render() matching Report Format Reference exactly
- test_tracer.py: 6 tests covering drift, clean, stage, best-failed score, empty inputs, path preservation
- test_reporter.py: 18 tests covering headers, sections, quoted text, en dash, score formatting, verdict block, presence/absence conditionals
- No modifications to matcher.py, parser.py, or models.py during Phase 3 execution (models.py was updated in pre-Phase 3 surgical fix only).
Next: Phase 4 — CLI, semantic extension, integration. See PHASE4_NS.md.

---

## Session 3 — Phase 4 Complete

### AD-19 — Optional sentence-transformers imported lazily inside matcher function body
**Decision:** `sentence_transformers` is imported inside `match_passages()`, inside the `if semantic:` branch, not at module top level. If the import fails, `ImportError` is raised with a user-facing install instruction.
**Reason:** `sentence-transformers` is not installed in the base environment (it is only listed in `requirements-semantic.txt`). A top-level import would crash module load for every process — including the 43 existing tests that never touch the semantic path. Keeping the dependency optional requires the module to be importable without it.
**Closes:** CB-1 from Phase 4 pre-build vetting. Top-level import would have broken all Phase 1–3 tests.

---

### AD-20 — Verdict immutability at CLI boundary
**Decision:** When `sem_debug.py` promotes DRIFT to BLOCKED, it creates a new `Verdict(status="BLOCKED", exit_code=2)` instead of mutating the existing object.
**Reason:** `Verdict` is a mutable dataclass. Mutating it in-place leaks the CLI layer's policy decision into the library object, which `tracer.trace()` also holds a reference to. Creating a new object preserves the library contract while allowing the CLI to enforce policy.
**Closes:** HI-1 from MVP_VET.md. Side-effect leak bug.

---

### AD-21 — Argparse manual validation to reserve exit code 2
**Decision:** `--inputs` is never marked `required=True` in argparse. Instead, it is parsed normally and manually validated after `parse_args()`. Empty `--inputs` prints to stderr and calls `sys.exit(1)`.
**Reason:** argparse's built-in missing-argument handler calls `sys.exit(2)` on Windows, which collides with BLOCKED (exit 2). Manual validation guarantees exit 1 for argument errors, keeping exit 2 exclusively for `--strict` / BLOCKED.
**Closes:** CB-2 from Phase 4 pre-build vetting.

---

### AD-22 — CLI entry point wrapped in main() with standard guard
**Decision:** `sem_debug.py` exposes all CLI logic inside `main()` and calls it only under `if __name__ == "__main__": main()`. No `sys.exit()` or `argparse.parse_args()` executes at import time.
**Reason:** Preventing module-level side effects keeps `sem_debug.py` import-safe for integration tests, coverage tools, or programmatic reuse without killing the interpreter.
**Closes:** MI-2 from Phase 4 vetting report.

---

### AD-23 — Exit codes documented in CLI help epilog
**Decision:** `ArgumentParser` receives an `epilog` containing the exact exit codes: `0=CLEAN, 1=DRIFT, 2=BLOCKED`. This string appears at the bottom of `--help` output.
**Reason:** The plan (PHASE4_NS_REV.md Step 4.3 item 10) mandates exit-code documentation. Initial implementation omitted the epilog; it was added after vetting flagged the gap. The epilog is the standard argparse placement for supplementary contract text.
**Closes:** D-1 from Step 4.3 vetting report.

AD-24 — Package refactored into proper installable structure
Decision: All source modules moved from flat workspace root into sem_debug/ package directory. Imports converted to explicit relative. Entry point updated to sem_debug.cli:main. pyproject.toml updated with [tool.hatch.build.targets.wheel] packages = ["sem_debug"].
Reason: Flat module layout caused pip install . to package only sem_debug.py, leaving all sibling modules behind. Post-install sem_debug --help crashed with ModuleNotFoundError: No module named 'models'. Package structure is the standard fix.
Closes: Task 3 install block (commit c22579f).

AD-25 — Semantic rescue validated with real embeddings
Decision: --semantic flag graduates from experimental. Zone 2 paraphrase fixture scored 0.4532 against all-MiniLM-L6-v2 embeddings, above the 0.35 threshold. Passage appeared in attributed output with method=semantic.
Reason: Task 2 required a score on record before shipping. Threshold passed. Caveat removed from KNOWN_LIMITATIONS.md.
Closes: Task 2 validation gate.

AD-26 — Task 4 smoke test run on real ICM pipeline content
Decision: Real-content smoke test executed inside a cloned ICM script-to-animation workspace. Input: RESEARCH.md (operator-written). Output: semdebug-script.md (DeepSeek via Stage 01 contract). All 7 script passages attributed to source. Metadata header (brand vault content) correctly flagged unattributed at score 0.08. No crashes, no false negatives on real content.
Reason: Fixture-only validation is insufficient. Real content surfaces chunking behavior, threshold calibration, and report readability under realistic conditions.
Closes: Task 4 observational gate.

---

## Phase 4 Status: COMPLETE
Steps 4.0–4.6 done. 51/51 tests passing.
- `requirements.txt`: `scikit-learn`
- `matcher.py`: semantic extension with lazy import of `sentence_transformers` (`all-MiniLM-L6-v2`)
- `requirements-semantic.txt`: `sentence-transformers`, `torch`
- `sem_debug.py`: CLI entry point with argparse, manual `--inputs` validation, `--strict` promotion, exit-code epilog, `main()` guard
- `test_cli.py`: 8 subprocess-based black-box tests covering exit codes 0/1/2, stage flag, threshold flag, report file, semantic import fallback, missing-inputs error
- MVP_VET.md: full codebase review identifying HI-1 (fixed), HI-2, MI-1–5, LI-1–3; safety and architecture checklists completed
- No modifications to `parser.py`. `matcher.py` changes limited to semantic extension block only.

**Total test count:** 51/51 (Phase 1: 6, Phase 2: 12, Phase 3: 25, Phase 4: 8).

---

## Session 4 — v2 Complete (Phases 1–4)

### AD-27 — Frozen JSON schema as public subprocess contract
**Decision:** `TraceResult.to_dict()` shape is locked by `tests/test_json_contract.py`. The dict contains exactly 6 top-level keys: `status`, `exit_code`, `stage`, `threshold`, `attributed`, `unattributed`. No extra keys may be added without updating the contract test and the CLI `--help` epilog.
**Reason:** `research_loop` calls `sem_debug` via subprocess and parses the JSON output. Any schema drift breaks the integration silently. The contract test fails CI if `to_dict()` changes shape, forcing explicit coordination.
**Closes:** HI-1 from Phase 1 vet (field name drift), HI-2 from Phase 3 vet (cross-repo `flagged_passages` mismatch).

---

### AD-28 — Real `passage_index` via identity mapping through `output_passages`
**Decision:** `TraceResult` carries an `output_passages: list[Passage] | None` field. `to_dict()` maps `id(Passage)` against this list to emit the original file-level index, not a synthetic sequential counter.
**Reason:** Synthetic sequential indices (0, 1, 2...) are fragile — they change if passages are filtered or reordered. The original index in the output file is stable and meaningful to a human reading the trace. Identity mapping is safe because `match_passages` returns the same `Passage` instances that `tracer.py` parsed.
**Closes:** MI-1 from Phase 1 vet (`source_passage_index` naming), CB-1 from Phase 1 model alignment.

---

### AD-29 — Section-aware input loading via CONTEXT.md, H2-only, path-relative-to-context_md.parent
**Decision:** `tracer.py` accepts an optional `context_md: Path | None`. When present, `workspace_parser.read_context_md()` extracts the Inputs table (H2 `## Inputs`, first markdown table below it). Each declared source is resolved relative to `context_md.parent` (the stage/workspace directory). If a `Section` column is present, only that H2 section is read via `parse_file_sections()`.
**Reason:** ICM workspaces organize inputs by section. Loading whole files wastes matcher cycles on irrelevant sections and risks false negatives when unattributed content comes from a section that was never meant to be read. H2-only section boundaries keep the heuristic simple and deterministic. Path resolution against `context_md.parent` is correct because CONTEXT.md lives in the workspace root, while `output_file` may be in a `fixtures/` or `outputs/` subdirectory.
**Closes:** Phase 2 core deliverable. AD-05 (header merging) applies within sections exactly as globally.

---

## v2 Status: COMPLETE
Phases 1–4 done. 85/85 tests passing.
- `models.py`: `to_dict()` with identity-mapped `passage_index`, `source_line_start`, `Verdict.to_dict()`
- `reporter.py`: `render_json()` wrapper
- `cli.py`: `--format json`, `--json` shorthand, `--context-md`, `--report` for both formats, JSON schema epilog
- `tracer.py`: `context_md` parameter, path resolution relative to `context_md.parent`
- `parser.py`: `parse_file_sections()` with H2 state machine
- `workspace_parser.py`: `read_context_md()` with YAML frontmatter skip, markdown table parsing, fault-tolerant (never raises)
- `tests/test_json_contract.py`: 5 frozen contract tests
- `tests/test_calibration_sections.py`: 4 fixture-based integration tests
- `tests/fixtures/context_workspace/`: 5-file ICM workspace for section calibration

**Total test count:** 85/85 (Phase 1: 7, Phase 2: 12, Phase 3: 5, Phase 4: 4, plus 57 existing).