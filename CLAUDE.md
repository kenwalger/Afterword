# CLAUDE.md

Rules for any session working in this repository.

## Authority

- `docs/` is the source of truth. Before changing anything, read `README.md`, then `docs/` and `docs/adr/`, then `fixtures/README.md`.
- Do not contradict an ADR. If a task seems to require it, stop and ask.
- When evidence changes a claim, append a dated entry to `docs/CLAIMS.md`. Never rewrite the original claim.
- Any change to the taxonomy version (`TAXONOMY.md`) or the labeling-guide version (`LABELING-GUIDE.md`) must also review `docs/LABELING-FIELD-GUIDE.md`, update it where it no longer matches, and bump its version.

## Current stage

**Stage 0** of `docs/ROADMAP.md` is finishing in parallel with **Stage 1 to 3a groundwork** (plan approved 2026-10-03, session 4).

- Stage 0 done: skeleton, read-only DEV probe, capability matrix, volume baseline (C-009), corpus targets (Option 2: historical `dev`, prospective `test`; ADR-010 amended). Timed chronological reviews done (2026-10-03, recorded in `CLAIMS.md` 2026-10-04). Stage 0 gate decided 2026-10-04: continue as planned (C-012 added). Remaining, by the author: labeling the `dev` corpus, from 2026-10-04 with `--posts random --seed N`. Analyses of partial labels report publication-order and shuffled labels separately (`afterword.label_records.split_by_post_order`).
- Groundwork in scope, all of it independent of labels and real comment data, all through the service layer (ADR-012):
  1. Docs: `DATA-MODEL` v5, `PRIORITY-POLICY` clarifications, `EVALUATION` v4, model-boundary records in `PRIVACY-AND-BOUNDARIES` v3.
  2. Normalization `norm-v0.1` (separate from the labeling tool's `display-v0.1`) and edit detection by normalized text.
  3. Instruction pre-check `pc-v0.1` (ADR-008).
  4. Priority policy `pp-v0.1`, pure, recording `rule_applied`.
  5. Heuristic baseline B1 `hb-v0.1`.
  6. Synthetic adversarial set `fixtures/corpus/adversarial.jsonl`, including injection cases.
  7. SQLite store behind a repository interface (ADR-013), ingest from probe runs with lifecycle and purge (ADR-009).
  8. Classifier wrapper with schema-constrained output and an incremental cache.
  9. Providers: Ollama (primary, local) and Anthropic (secondary, `claude-haiku-4-5-20251001`).
  10. Service functions and CLI commands for the above.
  11. Benchmark of the two approved Ollama models on synthetic fixtures only.
- Checkpoint: after items 1 to 6, stop for the author to commit before items 7 to 11.

Orientation checks open items at their source, not in earlier session summaries: count the valid timing records under `reports/timing/` (`afterword.timing.load_valid`, aggregates only) and the label records under `fixtures/labels/` (`afterword.label_records`, counts only). Never print record contents. A summary that lists an item as open can be out of date.

Model calls, local or remote, run only on synthetic data. No real comment data goes to any model until the author says so and the model-boundary record for that path is signed off; the author runs real model passes in their own terminal. Claude may ingest saved probe runs into the local store when a session prompt asks for it (from 2026-10-07). Claude never reads real comment text, and reports counts and aggregates only.

The seeded, class-balanced dev subset for model runs (session 8, Part C) is in scope now that labels exist.

Still out of scope: shadow mode and sealing (Stage 3b/3c), `--set test` selection, review state, overrides, dispositions, any UI, and any write call to DEV.

The volume baseline is computed from an explicit probe run ID, recorded in the report. Never compute it from a run that includes test comments.

## Privacy

- No real comment text, commenter names, or handles in any committed file. Committed fixtures are synthetic and listed in a manifest with their provenance.
- Real payloads live only in git-ignored paths: `fixtures/dev-api/source/real/`, `fixtures/corpus/v*/`, `fixtures/labels/`, `reports/`, and the store `data/`.
- Do not open anything under `fixtures/dev-api/source/real/` or `data/`. Work only from `reports/probe/<run>/shapes.json`, `probe-findings.json`, and aggregate reports.
- `afterword label` and `afterword label-ui` are for the author's own machine. Never run either on real data, and never open their outputs (`fixtures/labels/`, `reports/timing/`). Build and test them against synthetic fixtures only.
- Sending real comment data to a model requires the model-boundary record in `docs/PRIVACY-AND-BOUNDARIES.md` first. That happens no earlier than Stage 3.

## Credentials (ADR-006)

- The DEV key is read from the `DEV_API_KEY` environment variable only, and only in `src/afterword/adapters/dev/client.py`.
- The Anthropic key is read from the `ANTHROPIC_API_KEY` environment variable only, and only in `src/afterword/providers/anthropic.py`. It goes in a request header, never in a prompt.
- Never print, log, or persist either key, and never put one in a fixture, report, exception message, or prompt. Credentials never leave the adapter or provider boundary.
- Do not open `.env`.
- The user runs any live command that needs the key, using `! uv run --env-file .env afterword <command>`. Never ask for the key or suggest passing it inline.

## Adapter boundary (ADR-001)

- Every DEV payload detail (`id_code`, `children`, `body_html`, `user`, endpoint paths) stays inside `src/afterword/adapters/dev/`.
- Code outside the adapter consumes `afterword.observations` (or, later, the canonical model) and never refers to DEV field names.
- CLI commands are thin transports over application service functions (ADR-012). Move existing commands behind service functions when they are next changed substantively; no standalone refactor.

## Storage and identity (ADR-013)

- Storage sits behind a repository interface that only `src/afterword/service.py` calls. SQLite-specific SQL stays inside the repository implementation.
- Records use stable string IDs (source IDs, otherwise UUIDs), never auto-increment integers, and UTC RFC 3339 timestamps. Stored rows hold no filesystem paths, hostnames, or OS usernames.
- The content author, credentials, and settings belong to a platform connection, never to a module-level constant.

## Code standards

- All functions, methods, and module-level variables in `src/` and `scripts/` have complete type hints, including return types. `tests/test_code_standards.py` enforces the module-level variables.
- Every public module, class, function, and method in `src/` and `scripts/` has a Sphinx-style (reST field list) docstring: `:param name:` for every parameter, `:type:` only where hints are insufficient, `:returns:`, `:yields:` for generators, no `:rtype:` (hints carry it), and `:raises:` for exceptions the caller should handle. Constructor parameters are documented in `__init__`.
- `tests/` needs neither, but test helpers and fixtures are typed.
- Configuration is in `pyproject.toml`: ruff with ANN and D (pep257 convention; `tests/` excluded from both), mypy strict over `src/` and `scripts/`, pydoclint in Sphinx style.

## Tests

- Tests never make live API calls. `tests/conftest.py` removes `DEV_API_KEY` and installs a respx router that fails any unmocked request. Keep it autouse.
- All of these must pass before any commit:
  1. `uv run ruff check .`
  2. `uv run ruff format --check .`
  3. `uv run mypy`
  4. `uv run pydoclint src scripts`
  5. `uv run pytest` (the project venv, Python 3.14)
  6. `uv run --isolated --python 3.12 pytest`
- The declared floor is Python 3.12; check 6 is what supports that claim. Keep `--isolated`: without it, `--python 3.12` rebuilds the project venv on 3.12, and later plain `uv run` commands silently test 3.12 again.
- Hooks (`git config core.hooksPath scripts/hooks`, once per clone):
  - `pre-commit` rejects staged files containing em-dashes or bidi control characters (`scripts/check_text.py`; `LICENSE` exempt), then runs the identity scan (`scripts/check_committable.py`) and checks 1 to 4.
  - `commit-msg` rejects em-dashes and bidi control characters in the commit message.
  - Both report counts and `file:line` positions only. Run pytest yourself.

## Friction log

There are two logs with different purposes:

- **Session notes** go in `friction-delight-logs/sessionN.md` (git-ignored), one file per session, numbered sequentially. Record every surprise there at the time it happens, using the entry template from `docs/FRICTION-LOG.md`. End each session with a session summary in the same file, including a "Scope pressure" section for anything that tried to enter scope and the decision made.
- **The public record** is `docs/friction-log/session-N.md`, one file per session, indexed by `docs/FRICTION-LOG.md`. At the end of each session, copy into `docs/friction-log/session-N.md` the entries that matter to the experiment (API behavior, design decisions, claims or ADRs affected) plus a short session summary, then add the session's pointer line to the index in `docs/FRICTION-LOG.md`. These entries must contain no real comment text, names, or handles. Entries already recorded are never reworded; a correction is a new, dated entry.

When unsure whether an entry belongs in the public record, include it.

## Writing

No em-dashes in any prose, docs, code comments, commit messages, or generated reports. Use a colon, comma, parentheses, or a new sentence instead.

## Attribution

Do not add AI attribution anywhere: no `Co-Authored-By` trailers, "Generated with" lines, or similar credits in code comments or commit messages.

## Git Workflow

Never commit. Write the message to `commit-message.txt` and stop.