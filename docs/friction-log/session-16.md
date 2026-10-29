# Session 16: pre-seal audit of the seal-path tooling (2026-10-29)

Curated from the session notes. No real comment text, names, or handles. Every check in this session ran on code and synthetic fixtures only; no command ran against the real store.

### 2026-10-29 18:13 - Deep audit of the seal path through the Decision Engine

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Before the seal on 2026-11-02, audit the code it depends on: `preregistration write`, `corpus export`, `corpus verify`, `preregistration posts`, `exclude-post`, and their tests.

**Expectation:** Mostly robustness findings, none touching the freeze table.

**Observation:** Run `aud_R4f7isAJvl`, deep panel of five voices, stakes "irreversible". Content sent: `preregistration.py` and `corpus.py` in full, the seal-path functions of `service.py` and `cli.py`, and the two test files. All five voices finished, each with verdict "has-serious-issues". 42 raw findings, 18 after deduplication: 11 fixed, 5 rejected as wrong with evidence, 2 left for the author. None required a change to the freeze table or the classification path.

**Evidence:** run ID above; the adjudication table in the next entry.

**Workaround:** None needed.

### 2026-10-29 18:36 - Adjudication of the 18 findings

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Verify each finding against the code: fix it with a test, or reject it with evidence.

**Expectation:** Some findings would not survive a look at the code.

**Observation:**

| # | Finding | Voices | Decision | Evidence |
|---|---|---|---|---|
| A | `verify` ignores the file hash; duplicate lines collapse | 1, 2, 3, 4, 5 | fixed | reproduced on synthetic records; `duplicates` now counted, the file hash required unless a record was withdrawn |
| B | any record marked `withdrawn` passes, whatever else changed | 1, 2, 3, 4, 5 | fixed | reproduced; the manifest now holds `metadata_sha256` per record, and a withdrawn record must match it, with null text and a date |
| C | export checks, then writes without exclusive create or cleanup; a partial export blocks the version | 1, 2, 4, 5 | fixed | both files created exclusively; the data file is removed if the manifest fails |
| D | `add_exclusion` truncates and rewrites the record in place | 1, 2, 3, 4, 5 | fixed | written beside it and swapped in (`os.replace`, the `redact.py` pattern) |
| E | `withdraw` rewrites the only frozen copy of the text in place | 3, 5 | fixed | same swap-in |
| F | `write_record` removes the target on any `OSError`, even when its own open failed | 3 | fixed | removal only after this call created the file |
| G | `write_preregistration` writes before checking the conditions | 2, 4 | fixed | the shadow-mode checks run before the write |
| H | `registered_at` floored to the second | 1, 5 | rejected | ADR-010 (amended) makes the recorded time the boundary; flooring moves it under a second earlier, inside the window where the runbook forbids publishing |
| I | the late-exclusion check misses labeled comments deleted since; the CLI cannot pick a label directory | 1, 3, 5 | first part fixed; second rejected | reproduced; every comment on the post now counts. All labels live in `unfrozen` (runbook, "Labels stay where they are") |
| J | U+2028, U+2029, U+0085 inside text split a JSONL record (`str.splitlines`) | 3, 4 | fixed for the corpus; the same reader elsewhere left for the author | reproduced: U+2028 and U+2029 survive `norm-v0.1` inside code blocks and in Markdown and plain text, so one real comment could have crashed `corpus verify` on seal day |
| K | manifest written with CRLF on Windows | 2, 3, 4, 5 | fixed (manifest); log part rejected | `.gitattributes` (`eol=lf`) already normalizes committed bytes; the working file differed. The redaction log is git-ignored and read line by line |
| L | no reconciliation sweep for withdrawals | 3 | rejected | every ingest passes all deleted or purged comments in the store, not only new ones, and `withdraw` skips records already withdrawn |
| M | nothing checks the record is append-only against the tag; `verify` does not compare `registered_at` | 3 | left for the author | optional hardening; git history and the pushed tag are the control today |
| N | unstated assumptions (local clock, membership recomputed) | 3 | rejected | not a defect: ADR-010 names the recorded time; runbook Step 5 documents the probe-to-record gap |
| O | export omits `dev` comments not yet ingested | 4 | rejected | by design and documented: runbook Step 5 and `store_as_of_sync_run` |
| P | `corpus_set_of` returns neither for a test-period comment with unknown `created_at` | 4 | left for the author | set membership (ADR-010) is outside this session's fix scope; the function's docstring and a test state the behavior; the module docstring is less precise |
| Q | store times assumed timezone-aware | 4 | rejected | the store writes and reads aware UTC times; comparing naive with aware raises `TypeError`, so it cannot pass silently |
| R | tests miss the risky paths | 2, 3, 4, 5 | fixed | 15 tests added, each failing first |

**Evidence:** `tests/test_corpus.py` and `tests/test_preregistration.py`, the tests under "Findings of the pre-seal deep audit".

**Workaround:** Fixes limited to `corpus.py`, `preregistration.py`, and the seal-path functions of `service.py`; `docs/COMMANDS.md` (v7) and `fixtures/README.md` describe the stricter `verify` and the manifest's new field.

### 2026-10-29 18:45 - Escapes for U+2028 arrived as the characters

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Write a test with U+2028 and U+2029 in synthetic text.

**Expectation:** Escape sequences in the test source.

**Observation:** The file held the literal characters (ruff RUF001 caught them), and a session-note heading did too. Same cause as session 2's bidi entry.

**Evidence:** `ruff check` output.

**Workaround:** Rewritten with `chr(0x2028)` and `chr(0x2029)`; a scan of every changed file finds no non-ASCII character.

## Session summary

- Deep audit `aud_R4f7isAJvl` of the seal-path tooling: 42 raw findings, 18 distinct, 11 fixed with tests, 5 rejected with evidence, 2 left for the author (M and P above).
- Also for the author: the U+2028 line-splitting bug in the corpus reader also exists in `shadow.read_ledger` and `shadow.read_sealed`, `label_records._read_jsonl`, and two readers in `labeling.py`. Sealed records and the ledger hold no free text, so they are not at risk; label records hold the author's typed reason and note. Not changed here: outside the preregistration and corpus tooling.
- The fixes themselves were not sent for a second external audit (one audit per logical change).

### Scope pressure

- Fixing the same reader in `shadow.py` and the label tools: declined, outside the session's fix scope; reported.
- Changing `corpus_set_of` for unknown creation times: declined, set membership is ADR-010's; reported.
- A git-tag check of the record: declined, new feature; reported.
