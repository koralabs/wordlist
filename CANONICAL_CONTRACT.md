# wordlist canonical contract

Builds the English word list used to reason about Handles and provides an offline command (`check_badword`) that asks the canonical protected-words policy in `@koralabs/kora-labs-common` whether a candidate handle is allowed. It mints and signs nothing.

1. The checker only asks the canonical policy (`ProtectedWords.checkAvailability` from the pinned package) and has no matching rules of its own.
2. A wrong or missing policy package (name or version) is an error with a non-zero exit, never a guess.
3. Candidates outside 1-15 ASCII characters are refused before the policy runs.
4. List generation is deterministic: lowercase, apostrophes removed, letters and hyphens only, length cap counts punctuation, sorted output.
5. The unminted-handle diff lists only words absent from the handles list fetched from api.handle.me.
