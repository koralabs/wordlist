# CLI and Data Contracts

## `make_wordlist.py` Arguments
- `--max-len` (default `15`)
- `--no-intersection` (switch to union mode)
- `--scowl-size` (default `70`)
- `--scowl-no-filter`
- `--wordlist` (repeatable)
- `--wiktextract-jsonl`
- `--wordfreq-disabled`
- `--wordfreq-list small|best|large`
- `--out` (default `wordlist.txt`)

## `compare_handles.py` Arguments
- `--wordlist` (default `wordlist.txt`)
- `--out` (default `unminted_handles.txt`)
- `--url` (default Handles endpoint)
- `--cache-path` (default `.cache/handles.txt`)
- `--max-len` (default `15`)
- `--timeout` (default `30`)

## File Contracts
- Input wordlist files: UTF-8, one token per line.
- Handles API text: newline-delimited handles.
- Output files are newline-delimited and end with a trailing newline.
