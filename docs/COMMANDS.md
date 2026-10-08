# Commands

**Version:** 1 (2026-10-08)

The full command reference, moved here from the README on 2026-10-08 so the README can serve as a front door. Nothing was dropped in the move. In what order to run these, and why, is in `WORKFLOW.md`.

Every command is the same on Windows, macOS, and Linux: run it from the repository root in any shell (PowerShell, Command Prompt, bash, zsh). Setup (clone, `uv sync`, and the `.env` file) is in the README, under "Try it on your own account".

## The DEV key

Commands that call DEV read a DEV API key (DEV Settings, Extensions) from `DEV_API_KEY`. Put it in a `.env` file at the repository root, which is git-ignored:

```text
DEV_API_KEY=<your DEV API key>
```

Only `probe` calls DEV. Every other command works from saved runs and the local store and needs no key.

## Probe, baseline, and labeling

One example of each command (run IDs are UTC timestamps printed by the probe):

```text
uv run --env-file .env afterword probe
uv run afterword label --run <run-id> --mode chronological --week 2026-09-07
uv run afterword label-ui --run <run-id>
uv run afterword label --run <run-id>
```

- `probe` is read-only (GET only). It saves raw payloads under git-ignored `fixtures/dev-api/source/real/<run-id>/` and value-free findings under `reports/probe/<run-id>/`. Its console output is counts and IDs only, safe to share.
- `--mode chronological` times a plain oldest-first read of one week (C-009) and asks at the end whether to record it as a valid timing.
- `label-ui` is the faster way to label. It serves one page on 127.0.0.1 and opens it in your browser; if the browser does not open, use the `open: http://127.0.0.1:8765/?t=<token>` line it prints (the whole URL, token included; it changes on every launch). Keys: `1` to `9` and `0` choose the class, letters toggle flags, Shift+`0` to `3` sets the prospective grade, `g` then `0` to `3` the retrospective grade, `e` types the reason, Enter saves, `p` shows the post, `h` shows the definitions, `s` skips, `q` stops. Each Enter writes the label at once. Stop with `q` in the page or Ctrl+C in the terminal (closing the tab leaves the server running); run the command again to resume with the next unlabeled comment.
- `label` labels the same batches in the terminal, one batch of at most 40 comments, then stops; run it again to continue. Use it for `--mode chronological` (timing exists only there) or without a browser. The two write the same records and can continue each other's work, but never run both at once. In the terminal, `q` at the `Save?` prompt saves the label, then stops; `q` at an earlier prompt leaves the comment on screen unsaved, and the tool says so.
- `uv run afterword label status --run <run-id>` prints labeling progress for the run: labeled, remaining, and labels by pass, by tool, and by post order (publication order or shuffled). Counts only, never classes or grades.
- `--pass calibration` (either tool) re-labels comments that already have an initial label, from scratch, with the earlier label hidden; `--ids <file>` picks which. Nothing is overwritten (`LABELING-GUIDE.md`).
- Either tool takes `--posts random --seed N`, which shuffles the order of posts reproducibly; comments within a post stay oldest first. Keep the same seed for a whole pass.
- The full labeling routine, including every shortcut, is in `WORKFLOW.md` (section 3).
- `uv run afterword baseline --run <run-id>` writes the C-009 volume report under `reports/`.

`label` and `label-ui` show comment text only on your own machine (terminal or local page) and need no key.

## The store and classifiers

Stage 1 to 3a groundwork; the store and B1 have run on real data since 2026-10-07, B2 on synthetic fixtures only:

```text
uv run afterword ingest --run <run-id>
uv run afterword connections
uv run afterword store-status
uv run afterword forget --connection <connection-id> --yes
uv run afterword classify --condition b1 --heuristic hb-v0.2
uv run afterword classify --condition b2 --model qwen3:4b-instruct-2507-q4_K_M
uv run afterword evaluate --condition b1 --heuristic hb-v0.2 --policy pp-v0.2
uv run afterword dev-subset --size 50 --seed 20261008
uv run afterword dev-analysis --model <ollama-model>
uv run afterword models verify
uv run afterword bench --synthetic --model <ollama-model>
```

- `ingest` reads a saved probe run into the local SQLite store (`data/`, git-ignored), oldest run first, applying the lifecycle rules and the ADR-009 purge. `forget` removes every record of one connection; without `--yes` it only counts.
- `classify` runs B1 (heuristic) or B2 (a local model through Ollama, whose model-boundary path is signed off) over stored comments from others, incrementally, and applies the priority policy. It refuses a provider whose path is not signed off and a model whose digest differs from its pin.
- `store-status` prints the store's comments by lifecycle state and its lifecycle events, counts only.
- `evaluate` scores cached B1 or B2 classifications against your `dev` labels under a policy version (`pp-v0.1`, or the candidate `pp-v0.2`), without running a model. It prints counts and writes a git-ignored report under `reports/eval/`; `--misses` also writes the IDs of consequential comments that were collapsed, for your own review.
- `dev-subset` draws a seeded, class-balanced subset of labeled `dev` comments and writes its IDs to a git-ignored file, for `classify --ids` and `evaluate --ids`. It prints counts only.
- `dev-analysis` counts, offline, which rule decided each tier for B1 and B2 under each policy, how often the pre-check fired and on what labels, B2's class against your labels, and comments by detected language; counts only, to a git-ignored report.
- `bench --synthetic` benchmarks a model on the committed synthetic sets only; its output is safe to share.

Every command takes `--help` for its full option list (`uv run afterword --help`, `uv run afterword probe --help`).
