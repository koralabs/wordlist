# Feature Matrix

| Area | Capability | Key Files |
| --- | --- | --- |
| Environment bootstrap | Install prerequisites, set up venv, fetch SCOWL source | `prep.sh` |
| Source ingestion | Read newline word lists and wiktextract JSONL | `make_wordlist.py` |
| Source merging | Intersection/union merge behavior | `make_wordlist.py` |
| Normalization/filtering | Lowercasing, apostrophe stripping, token regex, max-length filtering | `make_wordlist.py` |
| Handles comparison | Fetch/cached handles text and diff against generated words | `compare_handles.py` |
| Guardrail logic | Deterministic helper branch/line coverage target | `coverage_guardrail.py`, `tests/test_coverage_guardrail.py` |
| Coverage enforcement | Automated branch+line threshold script and artifact | `test_coverage.sh`, `test_coverage.report` |
