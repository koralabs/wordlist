# Workflow

## Typical Run
1. Bootstrap local dependencies and source corpora:
   - `./prep.sh`
2. Build filtered wordlist:
   - `./.venv/bin/python make_wordlist.py`
3. Compare against minted Handles:
   - `./.venv/bin/python compare_handles.py`

## Output Files
- `wordlist.txt`: filtered candidate words.
- `unminted_handles.txt`: candidates missing from fetched handles set.
- `.cache/handles.txt`: cached handles API response used for compare step.

## Cache Behavior
- If cache exists, compare flow prompts whether to reuse it.
- If cache is bypassed, handles list is fetched and cache is overwritten.
