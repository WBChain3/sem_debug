# VET REPORT — Phase 3

**Scope:** `tests/test_json_contract.py`, `cli.py` epilog, cross-repo integration  
**Test status:** 81/81 passing ✓  
**Deliverables:** 5 contract tests (`test_trace_result_dict_keys`, `test_attributed_match_dict_keys`, `test_unattributed_dict_keys`, `test_verdict_dict_keys`, `test_method_semantic_preserved`), updated help epilog

---

## Critical

### HI-1 — Stale key name in CLI help epilog (FIXED)

`cli.py` line 27 still printed `"source_passage_index": int` in the `--help` JSON schema. Actual JSON output renamed this to `source_line_start` during Phase 1 vet (MI-1). Public-facing inconsistency — any user reading `--help` would write a broken integration.

**Fix applied:** `source_passage_index` → `source_line_start` in epilog string. Verified via `python -m sem_debug.cli --help`.

### HI-2 — `research_loop` reads nonexistent `flagged_passages` field (BLOCKING, cross-repo)

`research_loop/agent_loop/trace.py` line 55:

```python
parsed.get("flagged_passages", [])
```

`sem_debug` JSON contract has never emitted this key. Unattributed passages live under `unattributed` with `text_preview`. The result: `research_loop` always receives `[]` for flagged passages, silently discarding every drift detail.

**Important:** Fixing this in `sem_debug` (adding `flagged_passages`) would break the frozen contract test (`test_trace_result_dict_keys` asserts exactly 6 top-level keys: `status`, `exit_code`, `stage`, `threshold`, `attributed`, `unattributed`). The right fix is in `research_loop/trace.py`: change `parsed.get("flagged_passages", [])` to collect `text_preview` from `parsed.get("unattributed", [])`.

This is a known issue — `sem_debug` side is correct and frozen.

---

## Medium

None.

## Low

**LI-1 — Scratch docs stale**

`docs/northstar_refs/01-03.md` still reference `source_passage_index` in a few places. Non-blocking — scratch files, not canonical. The single source of truth is `NORTHSTAR.md` (patched in prior turn).

---

## Gate Status

| Gate | Result |
|---|---|
| `pytest tests/test_json_contract.py -v` | 5/5 passing ✓ |
| `sem_debug --help` shows JSON schema | Verified post-fix ✓ |
| `pytest -x` full suite | 81/81 passing ✓ |

---

## Recommended Action

- **sem_debug:** Phase 3 complete. No further changes needed.
- **research_loop:** File a separate issue to patch `trace.py` to consume `unattributed` → `text_preview` instead of `flagged_passages`.

Proceed to Phase 4 (calibration fixtures + combo tests).
