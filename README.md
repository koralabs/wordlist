# Wordlist Builder
Generate a reasonably comprehensive English word list (<= 15 letters) from SCOWL, Wiktionary, and wordfreq.

## What it does
- Generates a list from a local SCOWL/SCOWLv2 repo. (https://github.com/en-wl/wordlist)
- Merges one or more newline-delimited word lists.
- Merges wordfreq tokens (if you install the package).
- Optionally merges English entries from a wiktextract JSONL dump. (https://www.wiktionary.org/)
- Keeps only words made of ASCII letters and hyphens (apostrophes are removed).
- Counts punctuation toward the length limit (e.g., hyphens count).

## Prep script
```sh
# (Linux targeted)
./prep.sh
```

Then run:
```sh
./.venv/bin/python make_wordlist.py
```

## Find unminted Handles
```sh
./.venv/bin/python compare_handles.py
```

## Tests
```sh
./.venv/bin/python -m unittest discover -s tests
```

Knobs:
- `--wordfreq-disabled`: disable wordfreq tokens (enabled by default)
- `--wordfreq-list small|best|large`: word usage frequency:
  - `small`: most conservative; fewest rare/noisy words
  - `best`: balanced; fewer rare words than `large`
  - `large`: broadest; highest coverage, most noise
- `--no-intersection`: disable intersection mode (union instead). Intersection is on by default
- `--scowl-size`: SCOWL size parameter - min `35` (less noise words), max (more noise words) `95`
- `--scowl-no-filter`: disable SCOWL's default word filter (increase noise words)

## Notes
- `prep.sh` downloads SCOWL and installs wordfreq in `.venv`.
- `make_wordlist.py` does not download any data. Provide sources like SCOWL/SCOWLv2, wiktextract output, or other lists you trust.
- `make_wordlist.py` builds `sources/scowl/scowl.db` if it does not exist.
- The script always caches the Handles list at `.cache/handles.txt`. If the cache exists, you'll be prompted to use it (the prompt includes the file timestamp).
