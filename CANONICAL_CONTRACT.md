# wordlist canonical contract

## Purpose and authority

I build and keep the English word list used to reason about Handles, and I give operators an offline command (`check_badword`) that asks the canonical protected-words policy whether a candidate handle is allowed. I do not mint, sign or hold keys. The policy itself lives in `@koralabs/kora-labs-common` (pinned in `package.json`); I do not copy or re-implement it.


This file and `.enclave` are the operator's gate: a PR that changes any path listed in `.enclave` and merges into `master` needs the operator's approval. Nothing here authorizes signing, spending, minting, burning or editing on-chain contracts or settings. Ecosystem rules (addresses correct 100% of the time, never double-mint, chain-accurate properties) are in the koralabs root `AGENTS.md`.

## Invariants (must never be violated)

1. **The checker only asks the canonical policy.** `check_badword.cjs` calls `ProtectedWords.checkAvailability` from the pinned `@koralabs/kora-labs-common` and has no matching rules of its own. Enforced by `tests/check_badword.test.cjs` (real policy, original false-safe regressions).
2. **A wrong or missing policy package is an error, never a guess.** Wrong name, wrong version or missing package exits non-zero. Enforced by `tests/check_badword.test.cjs`.
3. **Bad input is rejected, not classified.** Candidates outside 1-15 ASCII characters are refused before the policy runs. Enforced by `tests/check_badword.test.cjs`.
4. **The checker makes no network calls.** Enforced only by design and the test harness running offline; no test asserts it.
5. **List generation is deterministic and filtered.** Lowercase, apostrophes removed, letters and hyphens only, length cap counts punctuation, sorted output. Enforced by `tests/test_make_wordlist.py` and `tests/test_make_wordlist_main.py`.
6. **The unminted-handle diff lists only words absent from the handles list fetched from api.handle.me (cached locally).** Enforced by `tests/test_compare_handles.py` and `tests/test_compare_handles_main.py`.
7. **No secrets in this repo.** Not enforced by a test.

## Boundaries and known limits

- The word list files are data; whether a word is offensive or reserved is decided by the canonical policy, not by me.
- `prep.sh` installs system packages and clones SCOWL on the operator's machine; it is a local helper, never run in CI.
- Nothing here gates minting. Minting-time protection is in the minting repos.

## Refactors needed to enforce this

- Add a test that the checker opens no network sockets (invariant 4).
- Add a gate that no key or token string is committed (invariant 7).
- If `wordlist.txt` / `unminted_handles.txt` ever feed a production decision, add a test pinning that consumer to them.
