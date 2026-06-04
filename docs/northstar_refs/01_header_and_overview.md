# NORTHSTAR.md — sem_debug v2 Build Reference

**Plan source:** `PLAN.md` (vetted, PLAN_REP.md resolved)  
**Codebase state:** 51/51 tests passing, `sem_debug/` package with 6 modules + 8 test files  
**Build order:** Phase 1 → Phase 2 → Phase 3 → Phase 4 (sequential, no skipping)  
**Comment policy:** Every public function, class, and module-level constant gets a docstring. Complex logic blocks (heuristics, fallbacks, regex) get inline comments. Comments explain *why*, not *what* — the code already says what.

---

## Design Constraints (non-negotiable)

| Constraint | Rationale |
|---|---|
| Default behavior unchanged | `--format` default is `markdown`. All Phase 1–4 CLI invocations work identically. |
| No breaking changes to `TraceResult` fields | `attributed`, `unattributed`, `verdict` stay as declared. Additive only. |
| Subprocess-only public contract | `__init__.py` stays empty. External callers use `sem_debug --format json`. |
| `workspace_parser.py` import-clean | Imports: `pathlib`, `re`, `typing`. No `parser.py`, `tracer.py`, or `matcher.py` imports. |
| Section extraction heuristic, never crash | Malformed `CONTEXT.md` → log warning to stderr, fallback to whole-file reading. |

---

## Comment Standards

**Docstring format (all public functions/classes):**
```python
def to_dict(self) -> dict:
    """Return a flat dict representation for JSON serialization.

    Keys: verdict.status, verdict.exit_code, stage, threshold,
          attributed (list of dicts), unattributed (list of dicts).
    Each match dict contains: passage_index, source_file, source_passage_index,
    score, method ("tfidf" | "semantic").
    """
```

**Inline comment format (complex blocks):**
```python
# FALLBACK: If no Inputs table found, read the entire source file.
# This preserves the Phase 1–4 behavior for workspaces without CONTEXT.md.
```

**Rule:** If a function is >15 lines OR contains a conditional with >2 branches, it gets at least one inline comment explaining the branch rationale.

