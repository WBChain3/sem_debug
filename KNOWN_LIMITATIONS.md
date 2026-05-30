# Known Limitations

## Language and Environment Dependency

`sem_debug` requires Python 3.8 or higher, required for `from __future__ import annotations`.

Windows console default encoding (cp1252/cp437) cannot display U+2013 en dash. Terminal output may show replacement characters. The `--report FILE` path writes correct UTF-8 and is the recommended way to view output on Windows.

## Semantic Matching Experimental Status

The `--semantic` flag requires `sentence-transformers` and downloads the `all-MiniLM-L6-v2` model on first use (~80 MB from HuggingFace). No semantic rescue has been empirically validated with real embeddings in this build. TF-IDF remains the validated default. Semantic behavior should be treated as experimental until validated.

## Single Stage Boundary Only

`sem_debug` traces one output file against a set of input files. It does not compare draft N against draft N+1, track temporal drift across iterations, or instrument pipelines. Each invocation is an independent snapshot.

## Attribution Is Best-Match, Not Causal

Output passages are linked to their highest-scoring input passage. When multiple inputs overlap, the tool picks one winner. It cannot distinguish faithful reproduction from accidental lexical overlap, and it cannot prove the agent actually read the input passage before writing the output. Attribution is heuristic proximity, not causal provenance.

## Semantic Validation Threshold

The `--semantic` path uses a cosine-similarity threshold of 0.45 to decide whether an output passage is attributable to a given input zone. The current validated score is 0.4532 (Zone 2 attributed, threshold passed). This threshold is a single scalar — it does not adapt per zone, per model, or per document length. Zones with naturally lower lexical overlap with the output may fall below the bar even when the agent genuinely used them. Zone-level tuning is not yet implemented.
