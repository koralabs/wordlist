# wordlist PRD

## Summary
`wordlist` builds and filters English word candidates for Handle availability analysis. It produces:
- a normalized candidate word list (`wordlist.txt`),
- a diff list of words not present in minted Handles (`unminted_handles.txt`).

## Problem
Handle discovery/analysis workflows need a deterministic, reproducible way to generate high-signal word candidates from multiple lexical sources and compare them against minted Handle inventories.

## Users
- Internal Kora Labs tooling and research workflows.
- Operators evaluating available one-word Handle opportunities.

## Goals
- Merge words from SCOWL + optional user lists + optional wiktextract + optional wordfreq.
- Enforce normalization and filtering constraints (length, charset, punctuation behavior).
- Compare generated wordlist against fetched Handles API data.
- Keep test and coverage guardrails for scripts and helper logic.

## Non-Goals
- Minting or reservation execution.
- Real-time availability guarantees (analysis output is point-in-time).

## Functional Requirements
- `make_wordlist.py`:
  - load configured sources,
  - merge via intersection (default) or union,
  - apply token normalization + filtering,
  - write output list.
- `compare_handles.py`:
  - load generated wordlist,
  - fetch or reuse cached Handles list,
  - compute and write missing handles file.
- `prep.sh`:
  - bootstrap local environment (venv, dependencies, SCOWL source).

## Success Criteria
- Unit tests pass via unittest discover.
- Coverage guardrail passes with >=90% line and branch coverage.
- Docs describe source, filtering, cache, and comparison behavior.
