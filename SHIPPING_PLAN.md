
TASK 1 — Cosmetic fixes from MVP_VET
CODE task. All mechanical, no behavior changes. Run pytest after each file touched.
HI-1: sem_debug.py — replace in-place Verdict mutation with immutable assignment. verdict = Verdict(status="BLOCKED", exit_code=2)
HI-2: parser.py line 34 — delete comment_start = i, dead variable.
MI-1: models.py — remove field from dataclasses import, unused.
MI-2: tests/test_cli.py — remove import pytest, unused.
MI-3: tests/test_matcher.py — remove import pytest, unused.
MI-4: tests/test_parser.py — remove Passage from import, unused.
MI-5: tracer.py — remove Match and Passage from import if not used in type annotations, otherwise keep and add inline comment justifying presence.
Verification: pytest -x, 51 passing, zero failures.

TASK 2 — Semantic validation
CODE task. Confirm Zone 2 paraphrase rescue works with real embeddings before shipping.
Install sentence-transformers into requirements-semantic.txt environment. Run sem_debug against the existing Zone 2 fixture with --semantic flag. The paraphrase passage must score above 0.35 and appear in attributed passages, not unattributed. Report the actual score.
Two outcomes. If it passes, --semantic graduates from experimental, remove the experimental caveat from limitations doc. If it fails, adjust threshold or document the actual behavior and keep the caveat. Either outcome is acceptable. Shipping without knowing is not.
Verification: manual CLI run, reported score on record.

TASK 3 — Installable package
CODE task. Add pyproject.toml with entry point pointing at sem_debug.py. Minimum viable: package name, version, entry point, dependencies matching requirements.txt. No extras beyond what is needed to make pip install . work and sem_debug available as a command.
Verification: pip install . in a clean environment, run sem_debug --help, confirm clean exit.

TASK 4 — Real content smoke test
Manual task, operator runs this. Take any real output you have produced in your own workflow. Identify the inputs that produced it. Run sem_debug against it. Not a fixture, not designed content. The goal is to see chunking behavior, threshold calibration, and report readability on real content at realistic length. Note anything that looks wrong or surprising.
No pass/fail gate. This is observational. Findings either inform a patch before merge or get added to known limitations.
SHIPPING PLAN — sem_debug
Branch: shipping, cut from 9e6c284. Master stays clean until merge.

TASK 1 — Cosmetic fixes from MVP_VET
CODE task. All mechanical, no behavior changes. Run pytest after each file touched.
HI-1: sem_debug.py — replace in-place Verdict mutation with immutable assignment. verdict = Verdict(status="BLOCKED", exit_code=2)
HI-2: parser.py line 34 — delete comment_start = i, dead variable.
MI-1: models.py — remove field from dataclasses import, unused.
MI-2: tests/test_cli.py — remove import pytest, unused.
MI-3: tests/test_matcher.py — remove import pytest, unused.
MI-4: tests/test_parser.py — remove Passage from import, unused.
MI-5: tracer.py — remove Match and Passage from import if not used in type annotations, otherwise keep and add inline comment justifying presence.
Verification: pytest -x, 51 passing, zero failures.

TASK 2 — Semantic validation
CODE task. Confirm Zone 2 paraphrase rescue works with real embeddings before shipping.
Install sentence-transformers into requirements-semantic.txt environment. Run sem_debug against the existing Zone 2 fixture with --semantic flag. The paraphrase passage must score above 0.35 and appear in attributed passages, not unattributed. Report the actual score.
Two outcomes. If it passes, --semantic graduates from experimental, remove the experimental caveat from limitations doc. If it fails, adjust threshold or document the actual behavior and keep the caveat. Either outcome is acceptable. Shipping without knowing is not.
Verification: manual CLI run, reported score on record.

TASK 3 — Installable package
CODE task. Add pyproject.toml with entry point pointing at sem_debug.py. Minimum viable: package name, version, entry point, dependencies matching requirements.txt. No extras beyond what is needed to make pip install . work and sem_debug available as a command.
Verification: pip install . in a clean environment, run sem_debug --help, confirm clean exit.

TASK 4 — Real content smoke test
Manual task, operator runs this. Take any real output you have produced in your own workflow. Identify the inputs that produced it. Run sem_debug against it. Not a fixture, not designed content. The goal is to see chunking behavior, threshold calibration, and report readability on real content at realistic length. Note anything that looks wrong or surprising.
No pass/fail gate. This is observational. Findings either inform a patch before merge or get added to known limitations.

TASK 5 — Merge and tag
When tasks 1 through 4 are clean and any findings from task 4 are either patched or documented, merge shipping into master. Tag the commit as v0.1.0.
Update README with limitations section from the limitations doc before merge. That doc ships with the code.

ORDER IS FIXED. Do not start task 2 before task 1 is clean. Do not start task 3 before task 2 has a result on record. Task 4 can run in parallel with task 3 if you have content ready. Task 5 only after everything above is resolved.

