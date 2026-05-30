# Known Limitations

## Language and Environment Dependency

`sem_debug` requires Python 3.8 or higher, required for `from __future__ import annotations`.

Windows console default encoding (cp1252/cp437) cannot display U+2013 en dash. Terminal output may show replacement characters. The `--report FILE` path writes correct UTF-8 and is the recommended way to view output on Windows.

## Single Stage Boundary Only

`sem_debug` traces one output file against a set of input files. It does not compare draft N against draft N+1, track temporal drift across iterations, or instrument pipelines. Each invocation is an independent snapshot.

## Attribution Is Best-Match, Not Causal

Output passages are linked to their highest-scoring input passage. When multiple inputs overlap, the tool picks one winner. It cannot distinguish faithful reproduction from accidental lexical overlap, and it cannot prove the agent actually read the input passage before writing the output. Attribution is heuristic proximity, not causal provenance.

## Semantic Validation Threshold

The `--semantic` flag requires `sentence-transformers` and downloads the `all-MiniLM-L6-v2` model on first use (~80 MB from HuggingFace). Validated against a Zone 2 paraphrase fixture with real embeddings — score 0.4532, above the 0.35 attribution threshold. TF-IDF remains the default matching method. Use `--semantic` when TF-IDF fails on paraphrase-heavy content.
