# Using Afterword on your own account

**Version:** 2 (2026-10-08)

v2: saved probe runs are now redacted when a comment is deleted, and older runs are reduced to structure ("When a commenter deletes a comment", "How long saved runs keep text"). Read-only database commands no longer create a database.

This is the statement `PRIVACY-AND-BOUNDARIES.md` requires before another author uses Afterword ("External testing"). It covers what Afterword collects when you run it against your own DEV account, where that goes, what is sent to any model, what the tool can and cannot do, how your key is handled, and how to delete everything.

It describes the code as it is today. If it and the code disagree, the code is wrong or this file is out of date: please open an issue.

## In short

- Afterword runs on your machine and talks to DEV with your own API key, using read requests only. It never posts, comments, reacts, edits, deletes, hides, or follows anything.
- It saves copies of your posts and of the comments on them, as DEV returns them, in git-ignored folders inside your clone. Nothing is uploaded anywhere.
- The "Try it" steps in the README (`probe` and `baseline`) use no AI model at all.
- Deleting the folders listed under "Deleting your data" removes everything Afterword wrote.

## What is collected

`afterword probe` makes these requests to `https://dev.to`, one per second, every one a GET:

| Request | What it returns | What is kept |
| --- | --- | --- |
| Your account (`/api/users/me`) | Your profile, including your email address | Your numeric user ID only. Every other field, the email included, is removed before anything is saved. |
| Your published posts | Each post's metadata and body | Everything DEV returns. |
| The comments on each of your posts | Every comment and reply: its text (as HTML), timestamps, thread position, and the commenter's public DEV profile fields as DEV includes them (name, username, profile image links) | Everything DEV returns. |
| One comment fetched on its own | The same fields for one comment | Everything DEV returns. Used to compare the two endpoints. |
| Your account again, with a deliberately wrong key | An error | The error's shape. This request carries a fixed fake string, never your key; it records how DEV reports a bad key. |

Only your own published posts are read. Drafts, other people's posts, your followers, reactions on your account, and anything outside DEV are not requested. Afterword does not look commenters up anywhere else.

The comments are other people's words. They are public on DEV, but your saved copies are yours to protect: please do not publish them. The project's rules for anything published from this data (paraphrase, no names, no verbatim quotes without permission) are in `PRIVACY-AND-BOUNDARIES.md`, "Publishing results".

## Where it is stored

Everything stays in your clone, in folders git ignores, so a `git add` or a pull request cannot pick them up by accident.

| Folder | Written by | Contains |
| --- | --- | --- |
| `fixtures/dev-api/source/real/<run-id>/` | `probe` | The raw responses: your posts and every comment, with commenter profile fields. |
| `reports/probe/<run-id>/` | `probe` | Findings about the API (counts, field shapes, rate limits) and a comment index of opaque IDs, timestamps, and hashes. No comment text and no names. |
| `reports/baseline-<run-id>.md` and `.json` | `baseline` | Counts only: comments per post and per week, and how they are spread. |
| `data/afterword.sqlite3` | `ingest` and later commands | The local database, if you go beyond the "Try it" steps: posts, comments, and their history. Commands that only read it (`connections`, `store-status`, `forget` without `--yes`) never create it. |
| `reports/redactions.jsonl` | `ingest` | A record of every change `ingest` made to saved runs: run, comment ID, and date. No text. |
| `fixtures/labels/`, `reports/timing/` | `label`, `label-ui` | Your own labels and timing records, if you label. |
| `reports/eval/`, `reports/bench/` | `evaluate`, `dev-subset`, `dev-analysis`, `bench` | Counts, comment IDs, and synthetic results. |
| `.env` | You | Your DEV API key. |

## What is sent to a model provider

- **`probe` and `baseline`: nothing.** They use no model of any kind.
- **The heuristic classifier (`classify --condition b1`): nothing.** It is plain code.
- **The local model classifier (`classify --condition b2`, through Ollama): nothing leaves your machine.** Requests go to Ollama on `localhost` only, and Afterword refuses a non-local Ollama host unless you name one explicitly. You need to install Ollama and pull a model yourself; pulling a model contacts the Ollama registry, without any comment data. Exactly which fields of a comment the model sees is listed in `PRIVACY-AND-BOUNDARIES.md`, "Model boundary".
- **The remote provider (Anthropic): never sent your comments.** The code exists for a comparison, but `classify` refuses to send stored comments to it, because that path has not been signed off. The only command that can reach it is `bench --provider anthropic`, which sends the committed synthetic test sets only, and only if you set an Anthropic key yourself.

Afterword has no telemetry or analytics and makes no network requests besides those to DEV and, if you use them, your local Ollama and the synthetic benchmark above. The labeling page (`label-ui`) listens on `127.0.0.1` only, so no other machine can reach it. Installing it (`uv sync`) downloads Python packages from the Python Package Index, as any Python project does.

## What the tool can and cannot do

**Can:** read your published posts and the comments on them, save them locally, and compute counts, labels, and classifications on your machine.

**Cannot:** write anything to DEV. The DEV client in Afterword sends only GET requests: it has no code that posts, comments, replies, reacts, edits, deletes, hides, moderates, blocks, or follows. It also makes no decision on your behalf: classification orders what you read and never removes a comment from view.

What your DEV key itself permits is up to DEV, not Afterword. Treat it as a full credential for your account, and see "Your API key" below.

## Your API key

- Create a key in your DEV settings, under Extensions. Give it a name such as `afterword` so you can recognize it later.
- Put it in a `.env` file at the root of your clone, as `DEV_API_KEY=<your key>`. That file is git-ignored.
- Afterword reads the key from the `DEV_API_KEY` environment variable only, in one module (the DEV client), and sends it only in the `api-key` header of requests to `https://dev.to`.
- It never prints, logs, or saves the key: not in reports, saved responses, error messages, or anything sent to a model.
- When you are done, revoke the key in the same DEV settings page and delete `.env`.

## Deleting your data

If you only ran the "Try it" steps, delete the raw responses and the reports:

```text
# macOS and Linux
rm -rf fixtures/dev-api/source/real reports

# Windows (PowerShell)
Remove-Item -Recurse -Force fixtures\dev-api\source\real, reports
```

If you also used the database, first see what it holds, then remove it:

```text
uv run afterword connections
uv run afterword forget --connection <connection-id>
uv run afterword forget --connection <connection-id> --yes
```

`forget` without `--yes` only counts what it would delete. With `--yes` it deletes every database record for that connection, overwriting the deleted content in the file. It does not touch the raw responses or the reports, so delete those folders too. To remove the database itself, and any labels:

```text
# macOS and Linux
rm -rf data fixtures/labels fixtures/corpus/v*

# Windows (PowerShell)
Remove-Item -Recurse -Force data, fixtures\labels
Get-ChildItem fixtures\corpus -Directory -Filter "v*" | Remove-Item -Recurse -Force
```

Then revoke your key on DEV and delete `.env`. Deleting the whole clone also removes everything.

## When a commenter deletes a comment

Afterword notices a deletion when you ingest a newer probe run (`afterword ingest`): DEV either shows the comment as a placeholder, or the comment is missing from two runs in a row (ADR-009). That same ingest removes the comment's text from the database and redacts it in every saved run on your disk: its text and the commenter's name, handle, and profile fields go, and only its ID, its time, and its place in the thread stay. Saved runs are rewritten, never deleted, and each redaction is recorded in `reports/redactions.jsonl` (run, comment ID, date).

If you only ever run `probe` and `baseline`, nothing is ingested and nothing is redacted: delete runs you no longer need from `fixtures/dev-api/source/real/`.

## How long saved runs keep text

Each `ingest` keeps the newest three saved runs whole and reduces older ones to IDs, timestamps, counts, and thread structure: no comment text, no names or handles, no post titles or bodies. The volume counts from a reduced run stay the same. Choose a different number with `afterword ingest --run <run-id> --keep-runs N`.

Two kinds of run keep their text past that limit: a run newer than the one being ingested, and a run you labeled comments from (the labels depend on it). Deleted comments are still redacted in both. Runs are never deleted; to remove one, delete its folder.
