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

### AD-10 — DEFAULT_THRESHOLD is a named constant in models.py
**Decision:** The match score floor lives in `models.py` as `DEFAULT_THRESHOLD = 0.35`.
Not inline in matcher.py or the CLI.
**Reason:** Single source of truth. Threshold is provisional pending calibration
against real ICM workspace fixtures — having it in one place means one change
propagates everywhere.
**Open item:** 0.35 is unvalidated. Calibration pass required in Phase 2 against
real corpus sizes before the default ships.

---

## Phase 1 Status: COMPLETE
6/6 tests passing. No drift. No blockers.
Next: Phase 2 — TF-IDF matcher.