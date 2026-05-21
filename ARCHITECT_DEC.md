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
Next: Phase 3 — tracer.py + reporter.py