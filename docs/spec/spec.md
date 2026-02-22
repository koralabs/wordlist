# Technical Spec

## Architecture
- `make_wordlist.py`: source collection, normalization, filtering, merge, and output generation.
- `compare_handles.py`: handles API fetch/cache + set-diff output pipeline.
- `prep.sh`: environment bootstrapping and SCOWL source provisioning.

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
- Bash workflow script `prep.sh` is validated through unit tests and reported as `NA` for line/branch metrics in `test_coverage.report`.
