# Technical Spec

## Architecture
- `make_wordlist.py`: source collection, normalization, filtering, merge, and output generation.
- `compare_handles.py`: handles API fetch/cache + set-diff output pipeline.
- `prep.sh`: environment bootstrapping and SCOWL source provisioning.
- `check_badword.cjs`: offline CLI input validation and direct calls to `ProtectedWords.checkAvailability` from `@koralabs/kora-labs-common@6.9.3`; no copied policy or raw-list parsing.
- `check_badword.py`: compatibility launcher for that Node CLI, preserving arguments, output and exit code.

The canonical engine performs the actual number replacement, morphology, composition and contextual exception decisions. The CLI validates its documented 1–15-character ASCII candidate format before lowercasing and losslessly JSON-string-escapes output fields before joining the three-column table. It does not alter the canonical dataset or implement its own matching rules. Require Node.js 20+; resolve the installed package normally or use the explicit `--common-package` directory. Reject a missing/wrong-name/wrong-version package rather than guessing a fallback. No classification path performs HTTP.

## Data/Filtering Rules
- Tokens are normalized to lowercase and apostrophes are removed.
- Allowed token pattern: alphabetic segments joined by hyphen (`[A-Za-z]+(?:-[A-Za-z]+)*`).
- Punctuation counts toward max length checks.
- Output ordering is deterministic (`sorted(...)` behavior).

## Error Handling
- SCOWL subprocess failures are surfaced with stdout/stderr details.
- Wordfreq import errors return explicit runtime guidance.
- Wiktextract JSON decode failures are skipped per-line.

## Testing and Coverage
- Unit tests use unittest modules under `tests/`.
- Coverage guardrail script bootstraps isolated tooling in `.venv_coverage`.
- Guardrail threshold: >=90% line and branch coverage for measurable Python runtime scope.
- Current measured scope:
  - `make_wordlist.py`
  - `compare_handles.py`
- Real policy unit tests and Node/Python subprocess journeys: `npm test`. These cover original false-safe regressions, positive context, normalization, format boundaries, empty files and dependency/input failures; they do not prove exhaustive semantic equivalence for every input or future policy version.
- Bash workflow script `prep.sh` is validated through unit tests and reported as `NA` for line/branch metrics in `test_coverage.report`.
