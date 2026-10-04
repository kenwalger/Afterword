![Afterword Logo](img/Afterword_logo_color.png)

Assisted comment triage for technical publishing. A scoped experiment, not a product.

Afterword asks whether AI can reduce the part of a comment stream that needs immediate human review without hiding the comments that matter most.

**Core boundary:** the system may organize attention. It does not decide whose voice the author is permitted to hear.

## Status

Stage 0 of `docs/ROADMAP.md` is open for timing and labeling, with Stage 1 to 3a groundwork built ahead and tested on synthetic data only. V1 is DEV-only; other platforms are deferred until the primary experiment produces evidence.

Done:

- Experiment design (docs and ADRs), committed before any code.
- A read-only DEV probe (`afterword probe`) that verified the capability matrix, including edit and deletion behavior.
- The C-009 volume baseline (`afterword baseline --run <run>`): 432 comments from others across 138 posts, recent and spiky. Review time is not yet measured.
- A local labeling tool (`afterword label`), including a chronological timing mode for C-009.
- The corpus targets decision: the historical corpus is `dev`, and the test set is prospective (ADR-010, amended).
- A local browser labeling interface (`afterword label-ui`, session 5), writing the same records as `label`.
- Stage 1 to 3a groundwork, independent of labels and real data (sessions 4 and 5): the store with ingest, lifecycle, purge, and forget; the classifier wrapper `pr-v0.1`; the Ollama and Anthropic providers; and classification normalization (`norm-v0.1`) with edit detection by normalized text, the instruction pre-check (`pc-v0.1`), the priority policy (`pp-v0.1`) as tested code, the heuristic baseline B1 (`hb-v0.1`, a draft until tuned on `dev`), and the synthetic adversarial set. The Anthropic provider is tested against mocked HTTP only.

Open: timed chronological reviews and labeling (the author). No model has classified a real comment. Both local models were benchmarked on the synthetic sets only (`docs/benchmarks/`), with no model chosen.

## Quick start

Requires git and [uv](https://docs.astral.sh/uv/). uv installs a suitable Python (3.12 or later) if needed.

```text
git clone https://github.com/kenwalger/Afterword.git afterword
cd afterword
uv sync
git config core.hooksPath scripts/hooks
```

The last line installs the commit hooks; git does not carry it in a clone, so every fresh clone needs it once.

Commands that call DEV read a DEV API key (DEV Settings, Extensions) from `DEV_API_KEY`. Put it in a `.env` file at the repository root, which is git-ignored:

```text
DEV_API_KEY=<your DEV API key>
```

Then, one example of each command (run IDs are UTC timestamps printed by the probe):

```text
uv run --env-file .env afterword probe
uv run afterword label --run <run-id> --mode chronological --week 2026-09-07
uv run afterword label-ui --run <run-id>
uv run afterword label --run <run-id>
```

- `probe` is read-only (GET only). It saves raw payloads under git-ignored `fixtures/dev-api/source/real/<run-id>/` and value-free findings under `reports/probe/<run-id>/`. Its console output is counts and IDs only, safe to share.
- `--mode chronological` times a plain oldest-first read of one week (C-009) and asks at the end whether to record it as a valid timing.
- `label-ui` is the faster way to label. It serves one page on 127.0.0.1 and opens it in your browser; if the browser does not open, use the `open: http://127.0.0.1:8765/?t=<token>` line it prints (the whole URL, token included; it changes on every launch). Keys: `1` to `9` and `0` choose the class, letters toggle flags, Shift+`0` to `3` sets the prospective grade, `g` then `0` to `3` the retrospective grade, `e` types the reason, Enter saves, `h` shows the definitions, `s` skips, `q` stops. Each Enter writes the label at once. Stop with `q` in the page or Ctrl+C in the terminal (closing the tab leaves the server running); run the command again to resume with the next unlabeled comment.
- `label` labels the same batches in the terminal, one batch of at most 40 comments, then stops; run it again to continue. Use it for `--mode chronological` (timing exists only there) or without a browser. The two write the same records and can continue each other's work, but never run both at once.
- Either tool takes `--posts random --seed N`, which shuffles the order of posts reproducibly; comments within a post stay oldest first. Keep the same seed for a whole pass.
- The full labeling routine, including every shortcut, is in `docs/WORKFLOW.md` (section 3).
- `uv run afterword baseline --run <run-id>` writes the C-009 volume report under `reports/`.

The store and classifiers (Stage 1 to 3a groundwork; tested on synthetic fixtures only):

```text
uv run afterword ingest --run <run-id>
uv run afterword connections
uv run afterword forget --connection <connection-id> --yes
uv run afterword classify --condition b1
uv run afterword classify --condition b2 --model qwen3:4b-instruct-2507-q4_K_M
uv run afterword models verify
uv run afterword bench --synthetic --model <ollama-model>
```

- `ingest` reads a saved probe run into the local SQLite store (`data/`, git-ignored), oldest run first, applying the lifecycle rules and the ADR-009 purge. `forget` removes every record of one connection; without `--yes` it only counts.
- `classify` runs B1 (heuristic) or B2 (a local model through Ollama, whose model-boundary path is signed off) over stored comments from others, incrementally, and applies the priority policy. It refuses a provider whose path is not signed off and a model whose digest differs from its pin.
- `bench --synthetic` benchmarks a model on the committed synthetic sets only; its output is safe to share.

`label` and `label-ui` show comment text only on your own machine (terminal or local page) and need no key. In what order to run these, and why, is in `docs/WORKFLOW.md`.

## Development

The hooks are installed by `git config core.hooksPath scripts/hooks` (see Quick start). The `pre-commit` hook rejects staged files containing em-dashes or bidi control characters, then runs the identity scan (`scripts/check_committable.py`), ruff, ruff format, mypy, and pydoclint. The `commit-msg` hook rejects em-dashes and bidi control characters in the commit message. The full check list, including tests on both supported Pythons, is in `CLAUDE.md`:

```text
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy && uv run pydoclint src scripts
uv run pytest
uv run --isolated --python 3.12 pytest
```

Commands that call DEV read the key from `DEV_API_KEY` (for example `uv run --env-file .env afterword probe`). Real payloads, reports, and labels are written only to git-ignored paths.

## Reading order

1. `docs/PROJECT-BRIEF.md`: the question and why it matters
2. `docs/SCOPE.md`: what V1 is and is not
3. `docs/LABELING-GUIDE.md`: what "consequential" means and how ground truth is produced
4. `docs/TAXONOMY.md`: comment classes and flags
5. `docs/PRIORITY-POLICY.md`: how classes become priority, and where the review threshold sits
6. `docs/EVALUATION.md`: how the claims are tested
7. `docs/CLAIMS.md`: what is being claimed, before evidence exists
8. `docs/DATA-MODEL.md`
9. `docs/PRIVACY-AND-BOUNDARIES.md`
10. `docs/API-CAPABILITY-MATRIX.md`
11. `docs/ROADMAP.md`
12. `docs/WORKFLOW.md`: the operating protocol: fresh probe, timing before labeling, labeling sessions, and the weekly routine of the test period
13. `docs/LABELING-AT-SCALE.md`: a future design note for labeling beyond V1 (not V1 scope)
14. `docs/adr/`
15. `docs/proposals/`: changes under discussion, and accepted ones with their evidence
16. `docs/FRICTION-LOG.md`: the index of the friction log, with the entries in one file per session under `docs/friction-log/`
17. `docs/benchmarks/`: dated benchmark write-ups, informational only
18. `docs/BRAND.md`: how the name and logo are presented

## Public deliverable

The primary public artifact is the evaluation write-up: what was claimed, how it was measured, what the classifier missed and why. A negative or reframed result is a valid outcome and will be published as one.

## Name

An afterword is what comes after the text is finished. Comments are the afterword readers write. The project is about what the author does with it.

## License

Apache License 2.0 (`Apache-2.0`). See `LICENSE` and `NOTICE`.
