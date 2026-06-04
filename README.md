# sem_debug v2

Passage-level attribution tracer for AI pipeline outputs. Now with structured JSON output, CONTEXT.md section awareness, and a frozen subprocess contract for orchestrator integration.

## What it does

sem_debug takes an output file and a set of declared input files. It maps each passage in the output back to its highest-scoring source. Passages with no detectable source are flagged as unattributed. Those are the signal: where the agent invented, hallucinated, or imported outside knowledge.

## The gap it fills

Van Clief's ICM (section 6.2) declares which files a stage was given. sem_debug answers which passage in the output came from which part of those files. ICM gives you observability. sem_debug adds traceability. Built in response to the semantic debugging gap identified in Van Clief and McDermott (2026), Interpretable Context Methodology, arXiv:2603.16021.

## Setup

```bash
pip install .
```

For semantic matching (optional):

```bash
pip install -r requirements-semantic.txt
```

Note: the semantic install pulls torch and sentence-transformers. Expect 300-400 MB.

Requires Python 3.8 or higher.

![sem_debug install](assets/sem_debug_sandbox1.PNG)

## Usage

### Basic (markdown report)

```bash
sem_debug output.md --inputs input1.md input2.md
```

### JSON output (machine-readable)

```bash
sem_debug output.md --inputs input1.md --format json
sem_debug output.md --inputs input1.md --json           # shorthand
sem_debug output.md --inputs input1.md --format json --report result.json
```

### CONTEXT.md section-aware loading

```bash
sem_debug output.md --inputs input1.md input2.md --context-md CONTEXT.md
```

When `--context-md` is provided, sem_debug reads the Inputs table from the CONTEXT.md and loads only the declared sections from each source file. This shrinks the attribution surface to exactly what the stage declared it used.

### Common flags

| Flag | Description |
|------|-------------|
| `--inputs FILE [FILE...]` | One or more input source markdown files |
| `--context-md FILE` | ICM-style CONTEXT.md for section-aware input loading |
| `--format {markdown,json}` | Output format (default: markdown) |
| `--json` | Shorthand for `--format json` |
| `--semantic` | Enable semantic matching via sentence-transformers on TF-IDF failures |
| `--report FILE` | Write report to FILE instead of stdout |
| `--strict` | Promote DRIFT to BLOCKED (exit code 2) |
| `--stage LABEL` | Stage label for the trace report |
| `--threshold N` | Similarity threshold (default: 0.35) |

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | CLEAN — all passages attributed |
| 1 | DRIFT — one or more unattributed passages |
| 2 | BLOCKED — DRIFT with `--strict` enforced |

### JSON output schema

```json
{
  "status": "CLEAN|DRIFT|BLOCKED",
  "exit_code": 0|1|2,
  "stage": "string",
  "threshold": 0.35,
  "attributed": [
    {
      "passage_index": 0,
      "source_file": "input.md",
      "source_line_start": 12,
      "score": 0.4821,
      "method": "tfidf|semantic"
    }
  ],
  "unattributed": [
    {
      "passage_index": 2,
      "best_failed_score": 0.12,
      "text_preview": "First 80 chars of passage..."
    }
  ]
}
```

The schema is frozen by `tests/test_json_contract.py` — changing it breaks the test.

![sem_debug install](assets/sem_debug_sandbox2.PNG)

## Subprocess contract

sem_debug is designed to be called by orchestrators via subprocess. The public contract is:

1. Call `sem_debug output.md --inputs ... --format json`
2. Read stdout as JSON
3. Check `exit_code`: 0=CLEAN, 1=DRIFT, 2=BLOCKED
4. Read `unattributed` array for drift details

No programmatic import API is exposed. `__init__.py` stays empty by design.

## Test suite

```bash
pytest -x
```

**85 tests** covering attribution, calibration, JSON contract, section parsing, CLI subprocess, and semantic fallback.

## What is coming next (v3 ideas)

- Multi-stage drift tracking. Compare attribution across iterations of the same stage.
- Zone-level threshold tuning. Different document types need different similarity floors.
- Report integration. Link trace output back into the ICM stage context automatically.
- Enforceable section-loading. Prevent stages from reading undeclared sections.

## Known Limitations

See `KNOWN_LIMITATIONS.md` for full details.

- **Attribution is best-match, not causal.** The tool picks the highest-scoring input passage. It cannot prove the agent actually read it.
- **Section extraction is H2-only.** `parse_file_sections()` tracks `## ` headers as boundaries. Subheaders merge into their parent section.
- **Single snapshot.** Each invocation is independent. No temporal drift tracking across drafts.
- **Semantic matching is opt-in.** Requires `sentence-transformers` (~80 MB model download). TF-IDF is the fast default.
