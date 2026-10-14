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

## Offline Protected-Policy CLI
`python3 check_badword.py <handles_file.txt> [--common-package <directory>]`
or `node check_badword.cjs` with identical arguments. `--help` prints usage.

- Node.js 20+; canonical API `ProtectedWords.checkAvailability` in `@koralabs/kora-labs-common@6.9.3`. `package.json` pins that exact package version. Use an existing package directory or provision the declared dependency separately; the CLI does not install or fetch it.
- Default lookup uses Node's installed-package resolution. The explicit directory must contain that package's `package.json` and built `protectedWords` entry. Missing/wrong-version packages are errors.
- Input: UTF-8, one candidate per line. Trim surrounding whitespace, omit blank lines, lowercase only for classification; preserve the trimmed original spelling in output.
- Candidate format: 1–15 characters, ASCII uppercase/lowercase letters/digits/underscore/dot/hyphen. Validate the trimmed original before lowercasing for policy; Unicode lookalikes such as the Kelvin sign remain `INVALID`. Other inputs receive `INVALID` without policy lookup. This is candidate format, not the complete on-chain Handle grammar.
- Output: offline package/version disclaimer followed by tab-separated `HANDLE`, `STATUS`, `REASON`. Each data field is encoded as the interior of a JSON string (outer quotes omitted): tabs/control characters, quotes and literal backslashes are escaped losslessly. Split each data row on literal tabs into exactly three fields, then decode each with `JSON.parse('"' + field + '"')`. This recovers the trimmed original spelling, including invalid candidates; invalid rows are never discarded to repair the table. `OK` means the installed policy permits the candidate; `FLAGGED` includes the canonical reason; `INVALID` identifies input-format failure.
- Empty files output only the disclaimer/header. A completed table exits0, including flagged/invalid rows; malformed CLI options, inaccessible files, missing Node/dependency or policy execution errors exit nonzero and emit a stderr diagnostic.
- The packaged dataset is a versioned offline snapshot, not live fetched policy. No minted/reserved inventory lookup or availability guarantee. No copied word list or local semantic approximation.

## File Contracts
- Input wordlist files: UTF-8, one token per line.
- Handles API text: newline-delimited handles.
- Output files are newline-delimited and end with a trailing newline.
