# Session 16b: three pre-seal fixes from the session 16 audit (2026-10-29)

Curated from the session notes. No real comment text, names, or handles. Synthetic data only; no command ran against the real store; no external audit, at the author's instruction.

### 2026-10-29 18:45 - Every line-splitting call in src/

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Find every line split in `src/` that is not at line feeds only (session 16, finding J), and fix those that read stored records.

**Expectation:** The three modules named in session 16, and maybe one more.

**Observation:** Eight call sites in four files, plus three already splitting at LF only:

| Site | Reads | Decision |
|---|---|---|
| `shadow.py` `read_ledger` | committed ledger (written escaped) | fixed, for consistency |
| `shadow.py` `read_sealed` | sealed records (written unescaped) | fixed |
| `label_records.py` `_read_jsonl` | label records, including the author's typed reason and note (written unescaped) | fixed |
| `labeling.py` `_labeled_ids`, `_batch_ids` | label and batch records | fixed |
| `bench.py` `load_cases` | the committed synthetic JSONL sets | fixed |
| `bench.py` `_manifest` | the Markdown table in `fixtures/corpus/MANIFEST.md` | reported only: not records; a split row would make bench refuse the set, never pass it |
| `cli.py` `_only_ids`, `_id_file` | ID list files (`--ids`) | reported only: IDs, no text |
| `display.py`, `normalize.py`, `labeling.py` (display) | text | already LF only |

**Evidence:** `tests/test_line_separators.py`, five tests written to fail first with synthetic records holding U+2028 and U+2029, in a typed reason and note among them.

**Workaround:** None needed.

### 2026-10-29 18:55 - `corpus verify` checks `registered_at`; runbook note on unknown creation times

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Close finding M's `registered_at` half and record finding P as a known limitation (session 16).

**Expectation:** Small changes.

**Observation:** `verify` now fails when the manifest's `registered_at` differs from the preregistration record's, compared as times (the manifest writes `+00:00`, the record `Z`). A corpus exported before the record therefore fails once the record exists. `docs/PREREGISTRATION.md` v7 adds "Known limitations": a comment on a test-period post with an unknown creation time falls into neither set under ADR-010, and DEV supplies `created_at` on every comment in practice (707 of 707, `API-CAPABILITY-MATRIX.md`). Step 8 of seal day now says a corpus exported before step 6 fails `verify`.

**Evidence:** `tests/test_corpus.py`, two tests written to fail first.

**Workaround:** None needed.

## Session summary

- Six JSONL readers now split at LF only; `corpus verify` checks `registered_at`; the runbook names the unknown-creation-time limitation.
- Not changed: the bench manifest-table reader and the two ID-list readers (no stored records), and every writer.
- Checks: ruff, format, mypy, pydoclint clean; pytest 798 passed on 3.14 and 798 passed on 3.12 (`--isolated`).

### Scope pressure

- Writing label files with LF line endings: not done (writers out of scope; reading works).
