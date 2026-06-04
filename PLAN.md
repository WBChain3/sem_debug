# sem_debug v2 — Automation-Ready Drift Detection

**Branch:** `main` (post-MVP, Phase 4 complete)  
**Scope:** Additive features only. CLI path is preserved. No breaking changes to Phase 1–4 contracts.  
**Goal:** `sem_debug` can be called automatically by any orchestrator (including `research_loop`) and returns structured, machine-readable results without markdown parsing.

---

## Design Constraint

`sem_debug` is a standalone tool. It does not implement orchestrator policy (`accept | rerun | rerun_strict | abort`). It reports flags. The caller decides what to do with them.

---

## Phase 1 — Structured Output (`--format json`)

### What
Add a machine-readable output mode alongside the existing markdown report.

### Changes
- `models.py`: Add `TraceResult.to_dict() -> dict` and `Verdict.to_dict() -> dict`. Flat structure with primitive types only (strings, floats, lists of dicts). No nested dataclasses in JSON.
- `reporter.py`: Add `render_json(trace_result: TraceResult) -> str`. Uses `json.dumps(result.to_dict(), indent=2)`.
- `cli.py`: Add `--format {markdown,json}` argument. Default is `markdown` (preserves Phase 4 behavior). When `--format json`, output is JSON string to stdout, exit codes unchanged (0/1/2).
- `cli.py`: When `--report` is used with `--format json`, write JSON string to file.

### Verification Gates
1. `pytest -x` — all 51 Phase 1–4 tests still pass.
2. `sem_debug <fixture> --inputs <inputs> --format json` returns valid JSON, exit 0 or 1.
3. `sem_debug <fixture> --inputs <inputs> --format json --report report.json` writes file, stdout empty.
4. JSON schema check: `to_dict()` output contains keys `verdict`, `attributed`, `unattributed`, `stage`, `threshold`. No markdown artifacts.

### Risk
- `reporter.py` is heavily tested (18 tests). Adding JSON path must not touch `render()` markdown logic. Gate 1 enforces this.

---

## Phase 2 — CONTEXT.md Awareness (`--context-md`)

### What
Parse an ICM-style `CONTEXT.md` to discover declared input sections. Only those sections are read from the prior stage's output, shrinking the attribution surface.

### Changes
- `workspace_parser.py` (new module): `read_context_md(path: Path) -> ContextSpec`. Parses frontmatter + Inputs table. Returns list of `(source_file, section_name)` pairs. If no Inputs table, falls back to whole-file reading (current behavior).
- `parser.py`: Add `parse_file_sections(path, sections: list[str] | None) -> list[Passage]`. If `sections` is `None`, behaves like current `parse_file()`. If provided, extracts only the named sections (H2-delimited markdown sections). Sections not found → warn to stderr, skip.
- `tracer.py`: `trace()` gains optional `context_md: Path | None = None`. If provided, reads it, resolves input sources + sections, calls `parse_file_sections()` instead of `parse_file()`.
- `cli.py`: Add `--context-md PATH` argument. Passed through to `trace()`.

### Verification Gates
1. Unit test: `workspace_parser.py` parses a fixture `CONTEXT.md` with Inputs table → 3 sources, correct sections.
2. Unit test: `parse_file_sections()` extracts only named H2 sections, skips others.
3. Unit test: `trace()` with `context_md` produces smaller `input_passages` list than without.
4. Integration test: Full CLI run with `--context-md` produces identical verdict to manual `--inputs` when the Inputs table matches the same files.
5. `pytest -x` — all prior tests pass.

### Risk
- Markdown section extraction is heuristic (H2 headers). A section with no clear boundary produces edge cases. Document in `KNOWN_LIMITATIONS.md` if found.

---

## Phase 3 — Clean Subprocess Contract for `research_loop`

### What
`research_loop`'s `Trace.check()` currently guesses JSON format that doesn't exist. After Phase 1, `sem_debug` emits real JSON. This phase updates the integration contract — in `research_loop`, not here — but `sem_debug` must guarantee the contract is stable.

### Changes (in `sem_debug`)
- `cli.py`: Document the JSON schema in `--help` epilog (under exit codes). Guarantees stability.
- `cli.py`: Add `--json` as a shorthand for `--format json` (common convention, no conflict).
- Freeze the `to_dict()` schema as a public contract. Add a `tests/test_json_contract.py` that asserts the exact keys and types, failing if we accidentally break the shape.
- `__init__.py` stays empty by design. The public contract is subprocess-only (`sem_debug --format json`). No programmatic import path is exposed.

### Verification Gates
1. `test_json_contract.py` passes. Fails if `to_dict()` keys change.
2. `sem_debug --help` shows JSON schema description in epilog.
3. `research_loop` smoke test: swap `Trace.check()` to use `--format json`, confirm drift detection still works end-to-end.

### Risk
- This phase depends on `research_loop` codebase access. If unavailable, the contract is still validated by the frozen test.

---

## Phase 4 — Calibration & Section-Loading Tests

### What
Validate that section-loaded attribution is at least as reliable as whole-file attribution, and document any degradation.

### Changes
- `tests/fixtures/`: Add fixture workspace with `CONTEXT.md`, staged outputs, and expected attribution results.
- `test_calibration_sections.py` (new): Compare `trace()` with/without `--context-md` on the same content. Assert identical verdict. If scores differ, document why.
- `test_cli.py`: Add tests for `--format json`, `--json`, `--context-md`.

### Verification Gates
1. `pytest -x` — total test count equals prior count + new tests, all green.
2. Section-loaded vs whole-file: same unattributed passage count on fixture content.
3. `--semantic` + `--format json` together: valid JSON, `method=semantic` preserved in output.

---

## Out of Scope (explicit)

| Item | Reason |
|------|--------|
| Orchestrator action set (`accept/rerun/rerun_strict/abort`) | Belongs to the caller, not `sem_debug` |
| MCP server wrapping | `research_loop` already has an MCP server; `sem_debug` is a subprocess tool |
| Raw source capture / `runs/<uuid>/` archival | v3 concern, requires directory scaffolding outside tool scope |
| Severity ladder (critical/warning/info) | Community decision: binary flag only |
| Enforceable section-loading (prevent stage from reading undeclared sections) | v3 concern, requires sandboxing |

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| `--format json` breaks markdown default | Default stays `markdown`; JSON is opt-in. Gate 1 on every phase. |
| `CONTEXT.md` parsing is heuristic | Document fallback behavior (whole-file if parse fails). Never crash. |
| `to_dict()` schema drift breaks `research_loop` | Frozen contract test (`test_json_contract.py`) fails CI if shape changes. |
| Section extraction misses content due to malformed headers | Parser logs skipped sections to stderr; caller sees warnings. |
| Large write_file / patch calls on this model hit network-error | Build PLAN in chunks if >6KB (per established memory note). |

---

## Reference Docs

- `ARCHITECT_DEC.md` — Phase 1–4 decisions, especially AD-12 (tuple return), AD-16 (JSON deferred), AD-17 (semantic stays in matcher).
- `KNOWN_LIMITATIONS.md` — Current caveats to update if new ones surface.
- `design_sketch_carryover.md` — Community takeaways that shaped this plan.
- `ICM_REFERENCE.md` — Van Clief §6.2 context for section-loading rationale.
