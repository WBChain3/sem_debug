# sem_debug — passage-level attribution tracer for AI pipeline outputs.

## What it does

sem_debug takes an output file and a set of declared input files. It maps each passage in the output back to its highest-scoring source. Passages with no detectable source are flagged as unattributed. Those are the signal — where the agent invented, hallucinated, or imported outside knowledge.

## The gap it fills

Van Clief's ICM (§6.2) declares which files a stage was given. sem_debug answers which passage in the output came from which part of those files. ICM gives you observability. sem_debug adds traceability.

## Installation

```
pip install .
```

Requires Python 3.8+. For semantic matching:

```
pip install -r requirements-semantic.txt
```

## Usage

```
sem_debug output.md --inputs input1.md input2.md
sem_debug output.md --inputs input1.md --semantic
sem_debug output.md --inputs input1.md --report report.md
sem_debug output.md --inputs input1.md --strict
```

- `--inputs` — one or more input source markdown files.
- `--semantic` — enable semantic matching via sentence-transformers on TF-IDF failures.
- `--report FILE` — write markdown report to FILE instead of stdout.
- `--strict` — promote DRIFT to BLOCKED (exit code 2) when unattributed passages exist.
- `--stage LABEL` — stage label for the trace report.
- `--threshold N` — similarity threshold (default: 0.35).

Exit codes: 0=CLEAN, 1=DRIFT, 2=BLOCKED.

## Known Limitations

### Language and Environment Dependency

`sem_debug` requires Python 3.8 or higher, required for `from __future__ import annotations`.

Windows console default encoding (cp1252/cp437) cannot display U+2013 en dash. Terminal output may show replacement characters. The `--report FILE` path writes correct UTF-8 and is the recommended way to view output on Windows.

### Semantic Matching Experimental Status

The `--semantic` flag requires `sentence-transformers` and downloads the `all-MiniLM-L6-v2` model on first use (~80 MB from HuggingFace). Validated against a Zone 2 paraphrase fixture with real embeddings — score 0.4532, above the 0.35 attribution threshold. TF-IDF remains the default matching method. Use `--semantic` when TF-IDF fails on paraphrase-heavy content.

### Single Stage Boundary Only

`sem_debug` traces one output file against a set of input files. It does not compare draft N against draft N+1, track temporal drift across iterations, or instrument pipelines. Each invocation is an independent snapshot.

### Attribution Is Best-Match, Not Causal

Output passages are linked to their highest-scoring input passage. When multiple inputs overlap, the tool picks one winner. It cannot distinguish faithful reproduction from accidental lexical overlap, and it cannot prove the agent actually read the input passage before writing the output. Attribution is heuristic proximity, not causal provenance.

### Semantic Validation Threshold

The `--semantic` path uses a cosine-similarity threshold of 0.45 to decide whether an output passage is attributable to a given input zone. The current validated score is 0.4532 (Zone 2 attributed, threshold passed). This threshold is a single scalar — it does not adapt per zone, per model, or per document length. Zones with naturally lower lexical overlap with the output may fall below the bar even when the agent genuinely used them. Zone-level tuning is not yet implemented.

## Background

Built in response to the semantic debugging gap identified in Van Clief and McDermott (2026), "Interpretable Context Methodology," arXiv:2603.16021.
