# Wordlist Builder

## Contributor test policy

Tests and coverage run locally only, never in GitHub Actions, directly or through lifecycle scripts, composites, workflow templates, or shared helpers. Preserve local test commands. Build, lint, publication, deployment, and production guards remain permitted. Remove obsolete required test checks when retiring them.

Generate an English candidate word list, compare it against minted Handles, and classify candidates using the shared protected-word policy offline.

## Documentation
- [Docs Index](./docs/index.md)
- [Product Docs](./docs/product/index.md)
- [Spec Docs](./docs/spec/index.md)

## Core Commands
- `./prep.sh`
- `./.venv/bin/python make_wordlist.py`
- `./.venv/bin/python compare_handles.py`

## Offline Protected-Policy Check
Requires Node.js 20+ and `@koralabs/kora-labs-common@6.9.3` (declared in `package.json`). Reuse an installed package without fetching anything:

```bash
python3 check_badword.py unminted_handles.txt --common-package /path/to/node_modules/@koralabs/kora-labs-common
# Or: node check_badword.cjs unminted_handles.txt --common-package /path/to/package
```

With the dependency installed locally, omit `--common-package`. Classification uses the actual shared policy engine and packaged dataset; it never downloads a live word list. `OK` means only this policy version permits the candidate, not that it is unminted, reservable or currently available. See [CLI contracts](./docs/spec/cli-and-data-contracts.md#offline-protected-policy-cli).

## Local Validation
- `PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py'`
- `./test_coverage.sh`
- `npm test` (real installed policy dependency; Python entry-point journeys included)
