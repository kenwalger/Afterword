# Preregistration Runbook

**Version:** 7 (2026-10-29). v7 adds "Known limitations" (a test-period comment with an unknown creation time) and says that `corpus verify` also checks the manifest's `registered_at` against the record (session 16b). v6 records the author's threshold decisions (`EVALUATION.md` v22), adds `afterword preregistration write`, and makes Step 5 the full seal-day sequence; Part 1 is published after the seal and excluded by amendment. The thresholds, freeze table, command, and version `0.2.0` land first in a preparation commit; the seal commit holds the record and the corpus manifest, with its message in the git-ignored `seal-commit-message.txt`. v5 records the result of Step 1a (`EVALUATION.md` v21). v4 records the self-agreement result and the author's decisions (`EVALUATION.md` v20) and adds Step 1a, the calibration pass on the 150 publication-order labels under `lg-v0.7`. v3 adds the exclusion of posts about Afterword from the test set (`excluded_posts` in the record, `afterword preregistration posts` and `exclude-post`), after ADR-010's amendment of 2026-10-18, which also makes the recorded `registered_at` the boundary. v2 matched the commands built in session 12 (`self-agreement`, `label --set test`, `shadow`, `corpus`), adds the preregistration record (`registry/preregistration.json`) and the non-revealing `shadow status`, and says which files to commit each week. v1 was the author's draft, written before those commands existed.

A step-by-step checklist for getting Afterword from "dev labeling done" to "test period running," then through the test period to the result. Work through it top to bottom. Each step says who does it and what "done" looks like.

**Why this matters:** preregistration means writing down what will be measured and what counts as success *before* any test result exists, then sealing it with a public timestamp (a pushed git commit). After that commit, the rules do not change. That is what makes the final result trustworthy.

## Before you start

- **Command names here match the code as of session 12.** If one ever seems not to, check it before relying on it:

  ```powershell
  uv run afterword --help
  uv run afterword <command> --help
  ```

  and compare with `docs/COMMANDS.md`. If a name differs, the code and `COMMANDS.md` win; update this file.
- **Run long commands in your own terminal**, not through Claude Code, with the laptop plugged in and sleep set to Never (`docs/WORKFLOW.md`). Commands that use the model need Ollama running.
- **Before every commit**, check `git status`: no `.env`, nothing under `fixtures/dev-api/source/real/`, `fixtures/corpus/v*/`, `reports/`, `data/`, or `fixtures/labels/`, and no `commit-message.txt` or `seal-commit-message.txt`.
- **Never paste comment text** into Claude Code or anywhere else. Console output from these commands is counts, IDs, file paths, and hashes only, and is safe to share.
- **Labels stay where they are.** Every label, dev and test, goes to the default label directory (`fixtures/labels/unfrozen/`); a label's `corpus_set` field says which set it belongs to. Freezing the corpus as `v1` does not move them, and no command below needs `--corpus-version`.

### What gets committed, and when

All of these live under `registry/` and hold no comment text:

| File | Written by | Committed |
| --- | --- | --- |
| `registry/preregistration.json` | `afterword preregistration write` on seal day (Step 5); later exclusions by `afterword preregistration exclude-post` | in the preregistration commit, then with each exclusion |
| `registry/corpus-v1-dev.json` | `afterword corpus export --version v1` | in the preregistration commit |
| `registry/shadow-ledger.jsonl` | `afterword shadow run`, one line per sealed week | every week of the test period |
| `registry/reveal.json` | `afterword shadow reveal` | once, at the end |

---

## Phase 1: Get ready (before preregistration)

### Step 1. Self-agreement check (you, on or after 2026-10-22)

Checks that your labels are consistent enough to serve as ground truth.

1. Draw the list (counts only on screen). The seed is the one recorded for this check (session 11):

   ```powershell
   uv run afterword self-agreement draw --seed 20261018
   ```

   It prints the ID file it wrote (`reports/eval/self-agreement-<date>-s20261018.txt`) and the label command to use. Run it on or after 2026-10-22: before then, only your earliest labels are 14 days old. One draw per day and seed; the record of the draw sits beside the ID file.

2. Re-label those comments blind, in the label UI (about three batches; run the command again for each):

   ```powershell
   uv run afterword label-ui --run <latest-run-id> --pass self_agreement --ids <id-file-from-step-1>
   ```

   Grade as if you had never seen them. Do not look up your earlier labels.

3. Get the comparison:

   ```powershell
   uv run afterword self-agreement report
   ```

   It prints counts only: Cohen's kappa on class, agreement on the consequential split (2 or 3 against 0 or 1) with its interval and the direction of each change, and agreement on the grade. The comment IDs of every disagreement go to a git-ignored file it names, for your own review.

**Done when:** the report shows agreement on class (kappa) and on the consequential split.

**If agreement is poor:** stop here and bring the report to a Claude Code session. The labeling guide requires fixing it (likely a relabel of the affected part) before anything is frozen. Only then is the dropped calibration pass reconsidered.

**Result (2026-10-23):** 80 of 112 on the consequential split (the first sitting 53 of 80, the second 27 of 32), class kappa 0.358. Decided: the guide is revised to `lg-v0.7`, the calibration pass below is reinstated for the 150 publication-order labels, and no second self-agreement cycle runs before preregistration (`EVALUATION.md` v20).

### Step 1a. Calibration pass on the first 150 (you, under `lg-v0.7`)

Relabels the 150 publication-order `dev` labels from scratch under `lg-v0.7`. Read `LABELING-GUIDE.md` ("Grade 2 versus grade 1", "Technical extension versus conversational") and `LABELING-FIELD-GUIDE.md` v5 first.

```powershell
uv run afterword label-ui --run 20261018T173927Z --pass calibration --ids reports/eval/calibration-first150-lg-v0.7.txt
```

- Four batches (40, 40, 40, 30); the page offers the next batch, or run the command again to resume. Take a real break between batches.
- The earlier label is never shown; do not look it up.
- The tools warn when the run is more than 7 days old (from 2026-10-25 for `20261018T173927Z`). If you label after that, run a fresh full probe and ingest first, and use the new run ID.
- Check progress with `uv run afterword label status --run <run-id>` (counts only).

**Done when:** all 150 have a calibration label. Then bring it to a Claude Code session to recompute the `dev` results (label summary, oracle ceilings, B1 and B2 scores, the accrual estimate).

**Result (2026-10-26):** all 150 relabeled (2026-10-23 and 2026-10-26). 109 of 150 keep their consequential split; 30 entered consequential and 11 left it, so the 150 hold 58 consequential labels against 39. Every `dev` result is recomputed on 494 labels in `EVALUATION.md` v21.

### Step 2. Pick the preregistration date (you)

The test set only fills from **posts published after preregistration**. Pick a date when you expect to publish regularly for the following weeks. Write it down.

### Step 3. Bring dev up to date (you, a day or two before the date)

Run these in order. Step 5 repeats them on seal day, immediately before the record is written, so this step is optional when seal day is close.

```powershell
uv run --env-file .env afterword probe
```

Note the new run ID, then:

```powershell
uv run afterword ingest --run <new-run-id>
uv run afterword label status --run <new-run-id>
```

If `label status` shows unlabeled comments, label them:

```powershell
uv run afterword label-ui --run <new-run-id> --posts random --seed 20261004
```

Then classify anything new:

```powershell
uv run afterword classify --condition b1 --heuristic hb-v0.2
uv run afterword models verify
uv run afterword classify --condition b2 --model llama3.1:8b-instruct-q4_K_M
```

**Done when:** `label status` shows 0 remaining, and both classify runs report every comment OK.

### Step 4. The preregistration session (Claude Code, then you decide)

Start a new Claude Code session with this prompt:

```
This is the preregistration session for Afterword. Start fresh with the
usual orientation, checking records directly. Dev is fully labeled and
classified as of run <new-run-id>; the self-agreement report is done.
Do not commit anything.

1. Recompute the accrual estimate and the volume-split median from run
   <new-run-id>, recorded with the run ID.
2. Draft numeric registered thresholds for all five measures (recall,
   review reduction, SURFACE size, SURFACE precision, SURFACE capture),
   relative to the oracle under pp-v0.2, plus the rule for what counts
   as B2 meaningfully beating B1. Show the dev evidence behind each
   number. Put the draft in docs/proposals/ for my decision; do not
   write it into EVALUATION.md yet. 
   Include in the registered rules: posts about Afterword itself are
   excluded from the test set, and list which posts those are (Part 1
   and any later parts) by ID.
3. Prepare the freeze: list every version to be frozen (taxonomy,
   labeling guide, normalization, pre-check, policy, heuristic, prompt,
   Llama digest and options, application version), and draft
   registry/preregistration.json with registered_at left for me to set.
4. Add a short "Where this is headed" section to README.md: current
   stage, what happens next, and when results are expected, linking to
   docs/ROADMAP.md.
5. Label UI: add a read-only accrual status panel with the same counts
   as `afterword shadow status` (weeks elapsed, test comments labeled,
   whether each target is met; never the number graded 2 or 3, and
   never B1 or B2 output).

Then stop for my decisions on the thresholds.
```

When the draft thresholds come back, **you decide the numbers.** Ask yourself: "If the test came back exactly at this number, would I call that a success?" Then tell Claude Code to write the final thresholds into `EVALUATION.md`, record the frozen versions, and write `commit-message.txt` for the preregistration commit.

**The preregistration record** (`registry/preregistration.json`) is what makes `--set test` and shadow mode work. Every test-set tool reads it, and refuses to run without it. It holds:

**Decided 2026-10-26** (`EVALUATION.md` v22, "Registered thresholds" and "Frozen versions"; `docs/proposals/accepted/2026-10-26-registered-thresholds.md`). The record is written on seal day by `afterword preregistration write` (Step 5), which sets `registered_at` to the current UTC time and the other fields from the application's pins, and refuses if the record exists. It holds, for example:

```json
{
  "registered_at": "2026-11-02T18:00:00Z",
  "b1_heuristic": "hb-v0.2",
  "b2_provider": "ollama",
  "b2_model": "llama3.1:8b-instruct-q4_K_M",
  "b2_model_digest": "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
  "policy_version": "pp-v0.2",
  "num_ctx": 4096,
  "excluded_posts": []
}
```

- **`registered_at`** is the start of the test period, in UTC, with the `Z`: the moment `preregistration write` runs, shortly before the commit (Step 5). Every tool treats a post published after it as a test post, and a comment that arrives after it on an earlier post as belonging to neither set.
- **Publish nothing between `registered_at` and the pushed commit.** ADR-010 (amended 2026-10-18) defines test posts by the recorded `registered_at`, which the commit seals; the record is necessarily written a few minutes before that commit. Keeping the gap empty means the recorded time and the commit tell the same story.
- **`excluded_posts`** lists posts about Afterword itself, which are excluded from the test set (ADR-010). It starts empty. Part 1 is published after the seal (decided 2026-10-26), so it is a test-period post and is excluded by a recorded amendment before any of its comments is labeled (Phase 2, step 2), as are later Afterword posts.
- The other fields name the registered conditions. Shadow mode refuses to run if the digest is not the application's pin, the context size differs, or the policy or heuristic version is unknown.

**Done when:** `EVALUATION.md` contains the final numeric thresholds, the stopping rule, and the frozen version list (done 2026-10-26), and the full check list passes. The record and the frozen corpus are made on seal day (Step 5).

### Step 5. Seal day (you, in your own terminal)

Before you start: the preparation commit (thresholds, freeze table, `preregistration write`, version `0.2.0`) is already committed and pushed, so the seal commit holds only the record and the corpus manifest. Ollama running, the laptop plugged in, nothing to publish until the end of step 13. Run the tests first; they take about eight minutes and need no data:

```powershell
uv run pytest
uv run --isolated --python 3.12 pytest
```

Then, in order:

1. **Probe** (needs the key):

   ```powershell
   uv run --env-file .env afterword probe
   ```

   Note the run ID it prints.
2. **Ingest** it:

   ```powershell
   uv run afterword ingest --run <run-id>
   ```

3. **Label status:**

   ```powershell
   uv run afterword label status --run <run-id>
   ```

   If it shows comments remaining, label them (`uv run afterword label-ui --run <run-id> --posts random --seed 20261004`) and run `label status` again until it shows 0.
4. **Classify with B1:**

   ```powershell
   uv run afterword classify --condition b1 --heuristic hb-v0.2
   ```

5. **Classify with B2** (verify the model first):

   ```powershell
   uv run afterword models verify
   uv run afterword classify --condition b2 --model llama3.1:8b-instruct-q4_K_M
   ```

   Both classify runs should report every comment OK.
6. **Write the preregistration record.** This sets `registered_at` to now; from here on, publish nothing until step 13 is done.

   ```powershell
   uv run afterword preregistration write
   ```

   It prints `registered_at` and refuses if `registry/preregistration.json` already exists.
7. **Freeze the dev corpus** (after the record, so the set boundary is the registered one):

   ```powershell
   uv run afterword corpus export --version v1
   ```

   It writes `fixtures/corpus/v1/dev.jsonl` (git-ignored, with text) and `registry/corpus-v1-dev.json` (IDs and hashes only), once.
8. **Verify the corpus:**

   ```powershell
   uv run afterword corpus verify --version v1
   ```

   It must print `verified`. It also checks that the manifest's `registered_at` equals the record's, so a corpus exported before step 6 fails here. If not, stop and bring it to a Claude Code session.
9. **Fill in the seal commit message,** starting with the Ollama version:

   ```powershell
   ollama --version
   ```

   Open `seal-commit-message.txt` (git-ignored, at the repository root) and replace `OLLAMA_VERSION` with what it prints, `PROBE_RUN_ID` with the run ID from step 1, and `REGISTERED_AT` with the time step 6 printed.
10. **Commit** (check first: no `.env`, nothing under `fixtures/dev-api/source/real/`, `fixtures/corpus/v*/`, `fixtures/labels/`, `reports/`, or `data/`, and no `commit-message.txt` or `seal-commit-message.txt`; `registry/preregistration.json` and `registry/corpus-v1-dev.json` are there, and nothing else should be):

    ```powershell
    git add -A
    git status
    git commit -F seal-commit-message.txt
    ```

11. **Tag** it:

    ```powershell
    git tag -a prereg-v1 -m "Afterword preregistration"
    ```

12. **Push** the commit:

    ```powershell
    git push
    ```

13. **Push** the tag:

    ```powershell
    git push origin prereg-v1
    ```

Check the result, and write the hash and time in your notes:

```powershell
git log -1 --format="%H %ci"
```

**The test period has started:** posts published after `registered_at` count. Now publish Part 1. Once it is live, exclude it before labeling any of its comments (Phase 2, step 2): `afterword preregistration posts` for its ID, then `afterword preregistration exclude-post --post <post-id>`, commit, push.

A comment created between the probe (step 1) and `registered_at` (step 6) is a `dev` comment by ADR-010 but is not in the frozen corpus `v1`; keeping steps 1 to 6 close together keeps that gap small. `corpus verify` does not see it, and the export records the store's last sync run (`store_as_of_sync_run`) so it can be counted later.

**From this point on, do not change** the taxonomy, policy, prompt, heuristic, model, thresholds, or `registry/preregistration.json`. If something is genuinely broken, stop and bring it to a Claude Code session: a change after preregistration must be recorded as a deviation, not made quietly.

---

## Phase 2: The test period (weekly, about 20 to 30 minutes)

Pick a regular day. Each week, in order:

### 1. Fetch and store new comments

```powershell
uv run --env-file .env afterword probe
uv run afterword ingest --run <this-week-run-id>
```

`ingest` also withdraws any comment deleted upstream from the frozen corpus file (ADR-009). `corpus verify --version v1` then counts it as withdrawn, not changed.

### 2. If you published a post about Afterword this week, exclude it first

Part 1, Parts 2 and 3, and any other post about Afterword are excluded from the test set (ADR-010). Do this **before labeling any of its comments**:

```powershell
uv run afterword preregistration posts
uv run afterword preregistration exclude-post --post <post-id>
git add registry/preregistration.json
git commit -m "Exclude post <post-id> from the test set (about Afterword)"
git push
```

`preregistration posts` lists the posts published after preregistration, newest first, with their ID, date, whether each is a test post or excluded, its count of comments from others, and its title. `exclude-post` appends the exclusion to the record with the time it was recorded (`--reason` defaults to "post about Afterword"). It refuses a post published before preregistration, and a post whose test comments you have already labeled. If you forgot and labeled some, `--after-labeling` records the exclusion as late: a deviation the write-up reports. Comments on an excluded post leave every count and score, including any already sealed.

### 3. Label the new test comments, blind

```powershell
uv run afterword label-ui --run <this-week-run-id> --set test
```

The terminal first prints how many comments are in each set (dev, test, and neither).

- Label **before replying** to these comments whenever you can. If you already replied, that is recorded automatically; just label honestly.
- The UI never shows you what B1 or B2 said. If it ever does, stop and report it: that would break the blind test.

### 4. Run shadow mode and seal the week

```powershell
uv run afterword models verify
uv run afterword shadow run
```

It classifies the new test comments with B1 and B2, seals their outputs in a git-ignored file under `reports/shadow/`, and prints that file, its SHA-256, and counts. It prints nothing about what either classifier said. It also appends the week's hash to `registry/shadow-ledger.jsonl`. Commit that file:

```powershell
git add registry/shadow-ledger.jsonl
git status
git commit -m "Shadow week <N>: <first 12 characters of the sha256>"
git push
```

- If it says **"nothing new to seal"**, no test comment arrived since the last run; there is nothing to commit.
- If it reports comments **held back** (B2 failed, for example because Ollama was not running), they are retried next run. `--seal-failed` seals a failed output as failed instead, which the policy surfaces; use it only for a comment that keeps failing.
- An ordinary `afterword classify` never touches test comments. Only `shadow run` classifies them.

### 5. Check the stopping rule

```powershell
uv run afterword shadow status
```

It shows weeks elapsed, test comments labeled, and whether each target is **met or not yet**. It never shows how many test comments are graded 2 or 3, because a running count of grades could steer the next label. It reveals nothing. The test period ends when **both** of these are reached:

- 20 consequential test comments **and** 100 test comments in total,

or when **16 weeks** have passed since `registered_at`, whichever comes first.

### If you miss a week

No harm done. Next week's probe picks up everything since the last run, and `shadow run` seals every test comment not yet sealed. Just do the steps once, in order.

---

## Phase 3: The result (once)

When `shadow status` says the stopping rule is met:

1. **Stop labeling test comments.** Labels made after the reveal are excluded from scoring (they would not be blind).
2. **Verify** that every week's sealed outputs match their committed hashes:

   ```powershell
   uv run afterword shadow verify
   ```

   If it says anything other than "verified", stop and bring it to a Claude Code session. Do not reveal.

3. **Reveal, once:**

   ```powershell
   uv run afterword shadow reveal
   ```

   It checks the hashes and the stopping rule again, refuses if either fails, and writes `registry/reveal.json`. Commit it. From then on `shadow run` refuses: accrual has stopped.

4. **Score, once:**

   ```powershell
   uv run afterword shadow score
   ```

   It verifies the sealed files again, then prints the five primary measures for B1 and B2 under the registered policy, and writes the full counts, by post order and with the oracle, to `reports/eval/shadow-score-<time>.json`.

5. Start a Claude Code session to compare the score with the registered thresholds, do the consequential miss review, and write the evaluation report.
6. Write Part 3.

The score is computed once. Rerunning, retuning, or rescoring after the reveal turns a test result back into development evidence, and the write-up has to say so.

---

## Known limitations

- **A comment with an unknown creation time.** Under ADR-010 a comment belongs to a set by its post's publication time and its own creation time. The tools (`corpus_set_of`) put a comment whose creation time is unknown in neither set once the record exists, even on a post published after `registered_at`, so it is counted but never labeled, sealed, or scored. In practice this does not arise: DEV supplies `created_at` on every comment, deletion placeholders included (707 of 707 in the capability probe, `API-CAPABILITY-MATRIX.md`), and `label status` reports any undated comment in its `undated` count.

---

## Quick reference

| When | What | Who |
| --- | --- | --- |
| On or after 2026-10-22 | Self-agreement check (`self-agreement draw --seed 20261018`, relabel, `self-agreement report`) | You |
| Before seal day | Preregistration session, decide thresholds (done 2026-10-26) | Claude Code, then you |
| Seal day | Step 5: probe, ingest, label status, classify B1 and B2, `preregistration write`, `corpus export`, `corpus verify`, `ollama --version`, commit, tag, push | You |
| After the push (Part 1 is scheduled 2026-11-10) | Publish Part 1, exclude it (`preregistration exclude-post`), commit, push; add the link to the README | You |
| Weekly, 5 to 16 weeks | Probe, ingest, exclude any new Afterword post, `label-ui --set test`, `shadow run`, commit the ledger, `shadow status` | You |
| When the stopping rule hits | `shadow verify`, `shadow reveal`, commit the record, `shadow score`, write Part 3 | You, then Claude Code |
