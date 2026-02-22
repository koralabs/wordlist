# Wordlist Builder

Generate an English candidate word list and compare it against minted Handles.

## Documentation
- [Docs Index](./docs/index.md)
- [Product Docs](./docs/product/index.md)
- [Spec Docs](./docs/spec/index.md)

## Core Commands
- `./prep.sh`
- `./.venv/bin/python make_wordlist.py`
- `./.venv/bin/python compare_handles.py`

## Local Validation
- `PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py'`
- `./test_coverage.sh`
