# Commands

**Version:** 7 (2026-10-29)

v7 makes `corpus verify` stricter, after the pre-seal audit (session 16): without a withdrawal the file must also match its committed hash, a repeated record fails, and a record counts as withdrawn only if its text is gone and the rest of it still matches the manifest. `corpus export` and the withdrawals write their files so that an interrupted write leaves nothing half-written; `preregistration write` checks the conditions before it writes; `exclude-post` counts labels on comments deleted upstream since. Session 16b adds that `corpus verify` fails when the manifest's `registered_at` differs from the preregistration record's.

v6 adds `preregistration write`, which writes the preregistration record on seal day (`PREREGISTRATION.md`, Step 5).

v5 adds `preregistration posts` and `preregistration exclude-post` (posts about Afterword are excluded from the test set; ADR-010, amended 2026-10-18).

v4 adds `self-agreement draw` and `report`, `--set test` on the label tools, the `shadow` commands (`run`, `status`, `verify`, `reveal`, `score`), and `corpus export` and `verify`, all built in session 12. The order in which to use them is `PREREGISTRATION.md`.

v3 makes `pp-v0.2` the default policy of `classify` and `evaluate` (adopted 2026-10-18).

v2 adds `ingest --keep-runs` and the saved-run redaction (ADR-009, amended 2026-10-08), the plain-language `baseline` console summary, and read-only store commands that never create a database.

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
- `--set dev` (the default) or `--set test` (either tool, and `label status`) chooses the corpus set (ADR-010). Before preregistration every comment is `dev` and `--set test` is refused. Once `registry/preregistration.json` exists, `test` is the comments on posts published after its `registered_at`, `dev` the comments on earlier posts that arrived by then, and the rest belong to neither set; the tools print the three counts. Labels record their set, and `label status` counts one set at a time.
- The full labeling routine, including every shortcut, is in `WORKFLOW.md` (section 3).
- `uv run afterword baseline --run <run-id>` prints a plain-language summary of your comment volume, each figure with one line saying what it means, and writes the full C-009 volume report under `reports/`.

`label` and `label-ui` show comment text only on your own machine (terminal or local page) and need no key.

## The store and classifiers

Stage 1 to 3a groundwork; the store and B1 have run on real data since 2026-10-07, B2 on synthetic fixtures only:

```text
uv run afterword ingest --run <run-id>
uv run afterword ingest --run <run-id> --keep-runs 5
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

- `ingest` reads a saved probe run into the local SQLite store (`data/`, git-ignored), oldest run first, applying the lifecycle rules and the ADR-009 purge. It then redacts every comment deleted upstream from all saved runs, and reduces saved runs older than the newest `--keep-runs` (default 3) to IDs, timestamps, counts, and structure, except a run newer than the one ingested and a run labels were made from. Runs are never deleted; each change is logged in `reports/redactions.jsonl`. It prints counts and run IDs only. A reduced run cannot be ingested. `forget` removes every record of one connection; without `--yes` it only counts.
- `connections`, `store-status`, and `forget` never create the database. Without one they say so and exit 0.
- `classify` runs B1 (heuristic) or B2 (a local model through Ollama, whose model-boundary path is signed off) over stored comments from others, incrementally, and applies the priority policy. It refuses a provider whose path is not signed off and a model whose digest differs from its pin.
- `store-status` prints the store's comments by lifecycle state and its lifecycle events, counts only.
- `evaluate` scores cached B1 or B2 classifications against your `dev` labels under a policy version (`pp-v0.2`, the applied one and the default, or `pp-v0.1` for earlier results), without running a model. It prints counts and writes a git-ignored report under `reports/eval/`; `--misses` also writes the IDs of consequential comments that were collapsed, for your own review.
- `dev-subset` draws a seeded, class-balanced subset of labeled `dev` comments and writes its IDs to a git-ignored file, for `classify --ids` and `evaluate --ids`. It prints counts only.
- `dev-analysis` counts, offline, which rule decided each tier for B1 and B2 under each policy, how often the pre-check fired and on what labels, B2's class against your labels, and comments by detected language; counts only, to a git-ignored report.
- `bench --synthetic` benchmarks a model on the committed synthetic sets only; its output is safe to share.
- `classify` and `evaluate` work on `dev` only. Test comments are classified by `shadow run` alone, and test labels are scored by `shadow score` alone.

## Self-agreement, the frozen corpus, and shadow mode

```text
uv run afterword self-agreement draw --seed 20261018
uv run afterword self-agreement report
uv run afterword preregistration write
uv run afterword preregistration posts
uv run afterword preregistration exclude-post --post <post-id>
uv run afterword corpus export --version v1
uv run afterword corpus verify --version v1
uv run afterword shadow run
uv run afterword shadow status
uv run afterword shadow verify
uv run afterword shadow reveal
uv run afterword shadow score
```

- `self-agreement draw --seed N` draws the self-agreement sample by the rule in `LABELING-GUIDE.md`: every analysis label at least 14 days old is pooled; the sample is every pooled comment graded 2 or 3 plus 25 drawn at random from the pool with the seed. The IDs go to `reports/eval/self-agreement-<date>-s<seed>.txt` (git-ignored), with a JSON record of the draw beside it; one draw per day and seed. Label them with `--pass self_agreement --ids <file>`. Options: `--set`, `--corpus-version`.
- `self-agreement report` compares each self-agreement label with the comment's analysis label: Cohen's kappa on class, agreement on the consequential split (2 or 3 against 0 or 1) with its interval and the direction of each change, agreement on the grade, and relabels made less than 14 days after the original. Counts only on the console; the comment IDs of every disagreement, with what differs, go to a git-ignored file under `reports/eval/`.
- `corpus export --version v1` freezes one corpus set (`--set`, default `dev`): its records, with normalized text, to `fixtures/corpus/v1/<set>.jsonl` (git-ignored), and its manifest, IDs and hashes only, to `registry/corpus-v1-<set>.json`, to commit. A version is written once. `corpus verify` checks the file against the manifest and reports matched, withdrawn (ADR-009), changed, missing, extra, and repeated records, and whether the file hash matches; it exits 1 unless nothing changed beyond withdrawals, and, when nothing was withdrawn, unless the file hash matches; it also exits 1 unless the manifest's `registered_at` equals the preregistration record's (both absent counts as equal). Each `ingest` withdraws comments deleted upstream from every frozen corpus file: text removed, ID kept, logged in `reports/redactions.jsonl`.
- `preregistration write` writes `registry/preregistration.json`, once: `registered_at` is the current UTC time, to the second; the conditions are the registered ones (B1 `hb-v0.2`; B2 Ollama `llama3.1:8b-instruct-q4_K_M` with the application's pinned digest and context size; the current policy version), and `excluded_posts` starts empty. It prints `registered_at` and the conditions, and refuses, changing nothing, if the record already exists. Run it on seal day only: every tool reads the record as soon as it exists.
- `preregistration posts` lists the posts published after `registered_at`, newest first: post ID, publication date, `test` or `excluded`, the count of comments from others, and the title (the author's own text; nothing from a commenter). `preregistration exclude-post --post <id>` appends an exclusion to `registry/preregistration.json` with the time it was recorded (`--reason`, default "post about Afterword"), to commit. It refuses an unknown post, a post published before preregistration, a post already excluded, and a post whose test comments are already labeled unless `--after-labeling`, which records the exclusion as late. Comments on an excluded post belong to neither set: no labeling tool, `classify`, shadow run, export, count, or score includes them.
- `shadow run` (needs `registry/preregistration.json`) classifies the test comments not yet sealed with the registered B1 and B2, applies the registered policy, and seals one record per comment and condition (classifier, versions, class, flags, outcome, tier, rule; no text or explanation) in a new git-ignored file under `reports/shadow/`. It prints the file, its SHA-256, and counts, never an output, and appends the hash to `registry/shadow-ledger.jsonl`, to commit that week. It refuses if the record's digest, context size, policy, or heuristic does not match the application, if a sealed file no longer matches the ledger, or after the reveal. A comment whose B2 output failed is held back and retried next run, unless `--seal-failed`. Option: `--ollama-host`.
- `shadow status` prints weeks elapsed, test comments labeled, whether each stopping-rule target is met, and the ledger's state. It never shows outputs or the number of test comments graded 2 or 3.
- `shadow verify` checks every sealed file against the ledger: matched, hash differs, missing, or not in the ledger. It exits 1 unless every file matches.
- `shadow reveal` verifies the sealed files, applies the stopping rule (both 20 test comments graded 2 or 3 and 100 labeled, or 16 weeks), and only then writes `registry/reveal.json`, to commit. Once revealed, `shadow run` refuses.
- `shadow score` (after the reveal) verifies the sealed files again and scores B1 and B2 with their sealed tiers against the test labels made before the reveal, with the five primary measures, by post order, and the oracle beside them. Counts on the console; the full counts to `reports/eval/shadow-score-<time>.json`.

Every command takes `--help` for its full option list (`uv run afterword --help`, `uv run afterword probe --help`).
