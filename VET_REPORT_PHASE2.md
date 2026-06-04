# VET_REPORT_PHASE2.md — Pre-Build Vetting Report for Phase 2

**Date:** 2026-06-03  
**Phase:** Phase 2 — CONTEXT.md Awareness (`--context-md`)  
**Codebase state:** 73/73 tests passing (`pytest -x`).  
**Files changed:** `sem_debug/cli.py`, `sem_debug/parser.py`, `sem_debug/tracer.py`, `sem_debug/workspace_parser.py` (new), `tests/test_parser_sections.py` (new), `tests/test_tracer_context.py` (new), `tests/test_workspace_parser.py` (new).  

---

## Executive Summary

Phase 2 is **functionally complete and passing all tests**. Section-aware input loading works: `workspace_parser.py` parses ICM-style `CONTEXT.md`, `parse_file_sections()` extracts only named H2 sections, `tracer.py` wires both together, and the CLI exposes `--context-md`.  

**Three issues to fix before Phase 3:** one import leak (HI-1), one missing CLI test (MI-2), one performance note (MI-1). None are blockers — all tests pass. But fixing them now keeps the codebase clean.

**Verdict: PROCEED to Phase 3 after fixing HI-1, MI-2, and adding MI-1 comment.**

---

## Critical Blockers

*None.*

---

## High Issues

### HI-1 — `workspace_parser.py` leaks imported symbols into module namespace
- **File:** `sem_debug/workspace_parser.py`
- **Observation:** `from sem_debug import workspace_parser` shows `NamedTuple`, `Path`, `annotations`, `re`, `sys` in `dir()`. These are implementation imports leaking as public attributes.
- **Fix:** Add `__all__ = ["InputDecl", "read_context_md"]` at module level.
- **Why this matters:** Import hygiene. Future developers may mistake `workspace_parser.Path` for a public API.

---

## Medium Issues

### MI-1 — `parse_file_sections()` O(n×m) section lookup, no comment
- **File:** `sem_debug/parser.py` lines 101-110
- **Observation:** `_in_requested_section()` loops over all `section_ranges` for every block. With many sections and many blocks, this is O(n×m). In practice (ICM workspaces: 3-5 sections, 10-50 passages) it's negligible. But there's no comment acknowledging the complexity.
- **Fix:** Add inline comment: `# O(n×m) where n=blocks, m=section_ranges. Acceptable for ICM workspace sizes.`

### MI-2 — No subprocess CLI test for `--context-md`
- **File:** `tests/test_cli.py`
- **Observation:** The new `--context-md` flag is tested only via direct `trace()` calls in `test_tracer_context.py`. The CLI subprocess path is untested. Per NORTHSTAR.md Phase 2 CLI tests and LI-2 from Phase 1 vet, new CLI args must follow the subprocess pattern.
- **Fix:** Add one subprocess test in `test_cli.py`: `test_cli_context_md` — create a temp CONTEXT.md, run `sem_debug` with `--context-md`, assert exit code and status.

### MI-3 — `workspace_parser.py` frontmatter regex assumes top-of-file
- **File:** `sem_debug/workspace_parser.py` line 30
- **Observation:** `re.match(r"^---\n.*?\n---\n", text, re.DOTALL)` anchors to start of string. If there are blank lines or a byte-order mark before `---`, frontmatter is not skipped.
- **Fix:** Use `re.search` with `^---\s*$` on the first non-empty line, or `text.lstrip()` before matching. Not urgent — standard editors don't prepend blank lines to frontmatter.

---

## Low / Polish

### LI-1 — `parse_file_sections()` H2 boundary detection is regex-light
- **File:** `sem_debug/parser.py` lines 88-89
- **Observation:** `stripped.startswith("## ") and not stripped.startswith("###")` misses `##Title` (no space) and `## Title #` (trailing hash). The regex in `workspace_parser.py` (`^##\s+Inputs\s*$`) is stricter.
- **Mitigation:** Current fixtures don't trigger this. Document as known limitation if edge cases surface. No fix needed for v2.

### LI-2 — No test for code-block/comment skipping inside sections
- **File:** `tests/test_parser_sections.py`
- **Observation:** Tests verify basic H2 extraction but don't confirm that code blocks and HTML comments are skipped within sections. This is inherited from `parse_file()` but a section-specific regression test would be stronger.
- **Fix:** Add `test_section_with_code_block_skipped` — a section containing a fenced code block should produce no passages from that block.

### LI-3 — `tracer.py` docstring doesn't mention `context_md` type
- **File:** `sem_debug/tracer.py`
- **Observation:** The docstring says "If context_md is provided..." but doesn't state it's a `Path | None`. The type hint is visible but not documented.
- **Fix:** Update docstring: `context_md: Path to an ICM-style CONTEXT.md file, or None for whole-file input loading.`

---

## Test Count

| Phase | Expected | Actual | Delta |
|---|---|---|---|
| Phase 1 (new) | 7 | 10 | +3 (keys tests pulled from Phase 3) |
| Phase 2 (new) | 12 | 12 | — |
| Prior (Phase 1–4) | 51 | 51 | — |
| **Total** | **70** | **73** | **+3** |

All 73 passing. No regressions.

---

## Gate Check

| Gate | Status | Evidence |
|---|---|---|
| 1. `pytest -x` all 51 prior tests pass | ✅ | 51/51 confirmed |
| 2. `workspace_parser.py` import-clean | ⚠️ | Leaks `re`, `sys`, `Path` (HI-1) |
| 3. `parse_file_sections()` extracts only named H2 sections | ✅ | `test_parse_single_section`, `test_parse_multiple_sections` pass |
| 4. Subprocess with `--context-md` | ⚠️ | Untested at CLI level (MI-2) |
| 5. Malformed CONTEXT.md falls back | ✅ | `test_trace_context_md_falls_back` pass |

---

## Recommended Fix Order (before Phase 3)

1. **HI-1** (1 min): Add `__all__` to `workspace_parser.py`.
2. **MI-1** (1 min): Add O(n×m) complexity comment in `parser.py`.
3. **MI-2** (10 min): Add `test_cli_context_md` subprocess test to `test_cli.py`.
4. **LI-2** (5 min): Add `test_section_with_code_block_skipped` to `test_parser_sections.py`.
5. **LI-3** (1 min): Update `tracer.py` docstring.

**Total: ~20 minutes.** All tests should still pass after fixes.

---

## Risk for Phase 3

| Risk | Mitigation |
|---|---|
| `tracer.py` changes from Phase 2 may conflict with Phase 3 contract freeze | Both are additive. No overlap. |
| `workspace_parser.py` regex edge cases (MI-3) may surface in real ICM fixtures | Document in `KNOWN_LIMITATIONS.md` if found. |

---

*Read first. Verify second. Ship last.*
