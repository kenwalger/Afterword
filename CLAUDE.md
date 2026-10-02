# CLAUDE.md

Rules for any session working in this repository.

## Authority

- `docs/` is the source of truth. Before changing anything, read `README.md`, then `docs/` and `docs/adr/`, then `fixtures/README.md`.
- Do not contradict an ADR. If a task seems to require it, stop and ask.
- When evidence changes a claim, append a dated entry to `docs/CLAIMS.md`. Never rewrite the original claim.

## Current stage

**Stage 0** of `docs/ROADMAP.md`: skeleton, read-only DEV probe, volume baseline (C-009).

Out of scope until the roadmap says otherwise: classification, any LLM call, normalization beyond what the probe needs, the data model tables, any UI, and any write call to DEV.

The volume baseline is computed from an explicit probe run ID, recorded in the report. Never compute it from a run that includes test comments.

## Privacy

- No real comment text, commenter names, or handles in any committed file. Committed fixtures are synthetic and listed in a manifest with their provenance.
- Real payloads live only in git-ignored paths: `fixtures/dev-api/source/real/`, `fixtures/corpus/v*/`, `fixtures/labels/`, and `reports/`.
- Do not open anything under `fixtures/dev-api/source/real/`. Work only from `reports/probe/<run>/shapes.json`, `probe-findings.json`, and aggregate reports.
- Sending real comment data to a model requires the model-boundary record in `docs/PRIVACY-AND-BOUNDARIES.md` first. That happens no earlier than Stage 3.

## Credentials (ADR-006)

- The DEV key is read from the `DEV_API_KEY` environment variable only, and only in `src/afterword/adapters/dev/client.py`.
- Never print, log, or persist the key, and never put it in a fixture, report, exception message, or prompt. Credentials never leave the adapter boundary.
- Do not open `.env`.
- The user runs any live command that needs the key, using `! uv run --env-file .env afterword <command>`. Never ask for the key or suggest passing it inline.

## Adapter boundary (ADR-001)

- Every DEV payload detail (`id_code`, `children`, `body_html`, `user`, endpoint paths) stays inside `src/afterword/adapters/dev/`.
- Code outside the adapter consumes `afterword.observations` (or, later, the canonical model) and never refers to DEV field names.

## Tests

- Tests never make live API calls. `tests/conftest.py` removes `DEV_API_KEY` and installs a respx router that fails any unmocked request. Keep it autouse.
- `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .` must all pass.
- The declared floor is Python 3.12. Verify with `uv run --python 3.12 pytest` before claiming support.

## Friction log

There are two logs with different purposes:

- **Session notes** go in `friction-delight-logs/sessionN.md` (git-ignored), one file per session, numbered sequentially. Record every surprise there at the time it happens, using the entry template from `docs/FRICTION-LOG.md`. End each session with a session summary in the same file, including a "Scope pressure" section for anything that tried to enter scope and the decision made.
- **The public record** is `docs/FRICTION-LOG.md`. At the end of each session, copy into it the entries that matter to the experiment (API behavior, design decisions, claims or ADRs affected) plus a short session summary. These entries must contain no real comment text, names, or handles.

When unsure whether an entry belongs in the public record, include it.

## Writing

No em-dashes in any prose, docs, code comments, commit messages, or generated reports. Use a colon, comma, parentheses, or a new sentence instead.

## Attribution

Do not add AI attribution anywhere: no `Co-Authored-By` trailers, "Generated with" lines, or similar credits in code comments or commit messages.