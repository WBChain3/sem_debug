# NORTHSTAR2.md — Task 3: Package Refactor and Install Verification

**Branch:** `shipping`
**Base plan:** NORTHSTAR.md Phase 3
**Context:** Flat module layout (`sem_debug.py` + siblings at root) breaks `pip install .` because hatchling packages only the name-matching module, leaving `models.py`, `parser.py`, etc. behind. After install, `sem_debug --help` crashes with `ModuleNotFoundError: No module named 'models'`.

---

## Step-by-Step Plan

### Step 1 — Create package skeleton
- Create directory `sem_debug/`
- Create `sem_debug/__init__.py` (empty)

### Step 2 — Move all source modules into the package
- `models.py` → `sem_debug/models.py`
- `parser.py` → `sem_debug/parser.py`
- `matcher.py` → `sem_debug/matcher.py`
- `tracer.py` → `sem_debug/tracer.py`
- `reporter.py` → `sem_debug/reporter.py`

### Step 3 — Convert `sem_debug.py` → `sem_debug/cli.py`
- Copy current `sem_debug.py` content into `sem_debug/cli.py`
- Change imports to relative:
  - `from .models import Verdict`
  - `from .reporter import render`
  - `from .tracer import trace`
- Keep `main()` and `if __name__ == "__main__": main()`

### Step 4 — Update internal imports in all moved modules
- `sem_debug/matcher.py`: `from .models import DEFAULT_THRESHOLD, Match, Passage`
- `sem_debug/parser.py`: `from .models import Passage`
- `sem_debug/tracer.py`: `from .models import DEFAULT_THRESHOLD, Passage, TraceResult, Verdict` + `from .matcher import match_passages` + `from .parser import parse_file`
- `sem_debug/reporter.py`: `from .models import TraceResult, Verdict`

### Step 5 — Delete root `sem_debug.py`
- Must be removed to prevent import shadowing (file `sem_debug.py` takes priority over `sem_debug/` package in same directory)

### Step 6 — Update `pyproject.toml`
- Change entry point: `sem_debug = "sem_debug.cli:main"`
- Add hatchling directive:
  ```toml
  [tool.hatch.build.targets.wheel]
  packages = ["sem_debug"]
  ```

### Step 7 — Update test imports (absolute package references)
- `test_models.py`: `from sem_debug.models import DEFAULT_THRESHOLD`
- `test_parser.py`: `from sem_debug.parser import parse_file`
- `test_matcher.py`: `from sem_debug.matcher import match_passages` + `from sem_debug.models import Match, Passage`
- `test_tracer.py`: `from sem_debug.models import DEFAULT_THRESHOLD, Verdict` + `from sem_debug.tracer import trace`
- `test_reporter.py`: `from sem_debug.models import Match, Passage, TraceResult, Verdict` + `from sem_debug.reporter import render`
- `test_matcher_calibration.py`: `from sem_debug.matcher import match_passages` + `from sem_debug.models import DEFAULT_THRESHOLD` + `from sem_debug.parser import parse_file`

### Step 8 — Update `tests/test_cli.py` subprocess invocation
- Replace `[sys.executable, "sem_debug.py", *args]` with `[sys.executable, "-m", "sem_debug.cli", *args]`

**⚠️ Watch point:** The switch from direct file execution (`python sem_debug.py`) to module execution (`python -m sem_debug.cli`) is a behavior change in the test, not just an import update. If anything about the `-m` invocation differs from direct file invocation (exit codes, stderr formatting, `__name__` behavior), a test could go red in a way that's hard to distinguish from a real regression. The first `pytest -x` output after this specific change must be inspected carefully — compare return codes, stdout, and stderr against the pre-refactor baseline.

### Step 9 — Verify `tests/conftest.py` still valid
- No change required. `sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))` already adds workspace root, which is sufficient for `import sem_debug` to resolve the local package.

---

## Verification Gates (in order, stop on any failure)

1. **`pytest -x`** — expect exactly 51 passed, 0 failed. If count != 51, stop and report.
2. **Clean stale install artifact** — `pip uninstall sem_debug -y` to remove the old flat-module `sem_debug.py` from `site-packages`.
3. **`pip install .`** — expect wheel build and install to complete with no errors.
4. **`sem_debug --help`** — expect clean help output (description + epilog with exit codes), zero traceback, exit 0.

---

## Risks Flagged

- **Import shadowing:** If the old `sem_debug.py` remains in `site-packages`, it could still be found before the package. Gate 2 (uninstall first) mitigates this.
- **Subprocess CWD:** `python -m sem_debug.cli` relies on the subprocess running with workspace root as CWD. True under default `pytest` behavior.
- **Hatchling heuristic failure:** Without `packages = ["sem_debug"]` in `pyproject.toml`, hatchling might produce an empty or incorrect wheel.
- **`-m` invocation divergence:** As noted in Step 8, `python -m` behavior may differ subtly from `python file.py`. The first test run after Step 8 must be scrutinized.
