# sem_debug — PLAN.md

## What This Is

A standalone Python CLI that sits at ICM stage boundaries and traces output passages back
to the input files that caused them. Produces a markdown report. Exits with a typed
severity code. Lightweight by default, semantic matching available via flag.

Directly addresses the gap named in Van Clief & McDermott (arXiv:2603.16021) Section 6.2:
"ICM currently provides observability but not traceability."

---

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Attribution method | Post-hoc matching, no agent annotation | Agent-annotated provenance inherits agent hallucination risk |
| Default matcher | TF-IDF via scikit-learn | Ubiquitous, zero model download, works on any workspace |
| Semantic matcher | sentence-transformers, opt-in via `--semantic` | Catches paraphrase and conceptual drift; too heavy for default |
| Output format | Markdown trace report | Fits ICM's plain-text philosophy; human-readable at stage boundary |
| Exit codes | Typed: CLEAN / DRIFT / BLOCKED | Enables gate integration in any pipeline or shell script |
| Scope | Standalone CLI, no ICM modification required | Must work on any existing workspace without changes |
| Dependencies | scikit-learn required, sentence-transformers optional | Installable in one line; no server, no deployment |

---

## Architecture

```
sem_debug/
├── sem_debug.py          # CLI entry point
├── parser.py             # Markdown chunker — splits files into attributable passages
├── matcher.py            # TF-IDF matching (default) + embedding matching (--semantic)
├── tracer.py             # Walks input declarations, builds provenance graph
├── reporter.py           # Renders markdown trace report
├── models.py             # Dataclasses: Passage, Match, TraceResult, Verdict
├── requirements.txt      # scikit-learn only
├── requirements-semantic.txt  # sentence-transformers, torch
└── tests/
    ├── fixtures/          # Static markdown fixtures — no network, no live workspace
    ├── test_parser.py
    ├── test_matcher.py
    ├── test_tracer.py
    └── test_reporter.py
```

---

## Data Model

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
    score: float          # 0.0–1.0
    method: str           # "tfidf" | "semantic"

@dataclass
class TraceResult:
    stage: str
    output_file: str
    input_files: list[str]
    matches: list[Match]
    unattributed: list[Passage]   # output passages with no match above threshold

@dataclass
class Verdict:
    status: str           # "CLEAN" | "DRIFT" | "BLOCKED"
    exit_code: int        # 0 | 1 | 2
    summary: str
```

---

## CLI Interface

```
sem_debug <output_file> --inputs <file1> [file2 ...] [options]

Required:
  output_file               Stage output markdown file to trace

  --inputs FILE [FILE ...]  Input files declared in stage CONTEXT.md
                            (Layer 3 reference files + Layer 4 working artifacts)

Options:
  --stage NAME              Stage label for the report (e.g. "02_script")
  --threshold FLOAT         Match score floor, default 0.35
  --semantic                Use sentence-transformers in addition to TF-IDF
  --report FILE             Write trace report to file (default: stdout)
  --strict                  Exit BLOCKED on any unattributed passage (CI use)

Exit codes:
  0   CLEAN    All output passages attributed above threshold
  1   DRIFT    Some passages unattributed — review recommended
  2   BLOCKED  Unattributed passages exceed threshold or --strict fired
```

---

## Matching Logic

### Default (TF-IDF)

1. Chunk output file into passages (paragraph-level, ~3–8 sentences).
2. Chunk all declared input files into passages.
3. Build TF-IDF corpus from input passages.
4. For each output passage, score against all input passages.
5. Assign best match if score >= threshold. Mark unattributed if below.

### Semantic (--semantic flag)

Runs after TF-IDF. For any passage scored below threshold by TF-IDF:

1. Encode output passage and all input passages using sentence-transformers
   (`all-MiniLM-L6-v2` — 80MB, fast inference).
2. Compute cosine similarity.
3. If semantic score >= threshold, upgrade match status to attributed with method="semantic".
4. Passages that fail both remain unattributed.

TF-IDF runs first always. Semantic is a second pass on failures only — keeps it fast even
with the flag enabled.

---

## Report Format

```markdown
# sem_debug Trace Report
Stage: 02_script
Output: output/script_draft.md
Inputs: _config/voice.md, references/structure.md, ../01_research/output/research.md
Verdict: DRIFT
Unattributed: 2 of 14 passages

---

## Attributed Passages

### Passage 3 (lines 12–16)
> "The company's Q3 revenue declined sharply across all segments..."

Best match: ../01_research/output/research.md (lines 34–36) — score 0.81 [tfidf]
> "Q3 showed significant revenue contraction across business units..."

---

## Unattributed Passages

### Passage 7 (lines 31–33)
> "This represents a broader structural shift in the industry..."

No input passage scored above threshold (best: 0.21).
Possible causes: agent inference, hallucination, or missing input file.
Action: review this passage manually or re-run with --semantic.

---

## Verdict: DRIFT
2 passages could not be attributed to declared inputs.
Exit code: 1
```

---

## Phase Gates

### Phase 1 — Core data model and parser
- `models.py` complete with all dataclasses.
- `parser.py` chunks markdown into Passage objects correctly.
- Handles: empty files, single-paragraph files, code blocks (skip or flag), headers.
- Verification: `pytest tests/test_parser.py -x`

### Phase 2 — TF-IDF matcher
- `matcher.py` scores output passages against input corpus.
- Threshold logic correct — passages below floor go to unattributed.
- Verification: `pytest tests/test_matcher.py -x` against static fixtures.
- No network calls. No live workspace. Fixtures only.

### Phase 3 — Tracer and reporter
- `tracer.py` wires parser + matcher, builds TraceResult.
- `reporter.py` renders markdown from TraceResult.
- Verdict and exit code logic correct.
- Verification: `pytest tests/test_tracer.py tests/test_reporter.py -x`

### Phase 4 — CLI and integration
- `sem_debug.py` entry point wires all modules.
- `--semantic` flag imports sentence-transformers only when present; graceful error if not installed.
- End-to-end test against static fixtures: CLEAN case, DRIFT case, BLOCKED case.
- Verification: `pytest -x` full suite + manual CLI smoke test.

---

## Constraints

- All tests use static fixtures. No network. No live workspace.
- `except` blocks are typed — never bare `Exception` without comment.
- No subprocess, exec, or eval in application logic.
- `--semantic` import failure produces a clear user-facing error, not a traceback.
- Threshold default (0.35) is a named constant in `models.py`, not inline.
- Code block content in markdown is skipped by the parser (not attributed, not flagged).

---

## Out of Scope for MVP

- Automatic CONTEXT.md parsing to infer input files (future: `--auto` flag reads Inputs table).
- Cross-stage trace (tracing stage 3 drift back through stage 1) — single stage boundary only.
- Output edit tracking across runs (Section 6.3 of paper).
- GUI or web interface.

---

## How It Fits ICM

sem_debug requires no changes to any ICM workspace. It reads the same files ICM already
produces. The human runs it at a stage boundary before advancing, the same moment they
would open the folder and read manually. It does the reading for them and flags what needs
attention.

Van Clief's review gate + sem_debug = the proto-debugger he describes in Section 6.2,
shipped as a tool he can point to from the paper's repository.