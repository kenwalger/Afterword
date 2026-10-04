# Workflow

**Version:** 3 (2026-10-04)

v3 records both chronological timings as done (section 2), and adds to section 3 the terminal tool's save-on-quit rule, `afterword label status`, and the calibration pass.

v2 adds the browser labeling tool (`afterword label-ui`) and the `--posts random --seed N` post order to section 3.

The operating protocol: what to run, in what order, and what never to do, so that each measurement means what the other documents say it means. `LABELING-GUIDE.md` defines how to label; `EVALUATION.md` defines what is measured. This document is the routine that keeps both honest.

Commands assume the setup in the README's Quick start. Commands that call DEV read the key from `.env`; from a Claude Code session, the author runs them with a `!` prefix (`! uv run --env-file .env afterword probe`), so the key never enters the session.

## Rules that apply throughout

- Every measurement names the probe run it came from. Nothing picks a run implicitly.
- Never compute the baseline or label from a scoped run (`--article`) or from a run that includes hand-test comments.
- Practice is allowed, but it is never evidence. A timing run not confirmed as valid is saved under `reports/timing/practice/` and is ignored by every report.
- Label and timing outputs (`fixtures/labels/`, `reports/timing/`) are opened only by the author. Probe and baseline console output contains counts, statuses, and IDs only, and is safe to share.

## 1. Fresh probe first

Before a labeling or timing session, run a full probe:

```text
uv run --env-file .env afterword probe
```

The probe prints its start time, a single status line (requests sent, article N of total, and a countdown during any 429 wait), then its end time and elapsed time. A full run takes several minutes at one request per second. Note the run ID it prints.

Why: comments deleted upstream must not be labeled (ADR-009), and only full runs from `dev-probe-0.2` on carry every post's edit time, which `context_reconstructed` needs. `afterword label` warns when the run is more than 7 days old. Treat the warning as a stop, not a note.

If the run is `PARTIAL`, read its limitations before using it. An unexpected comment shape needs a friction entry first.

## 2. Timing before labeling

Chronological timing (C-009, condition B0) measures how long a plain oldest-first read of one week takes. Labeling is a close read, so a week timed after it is labeled measures a re-read of a re-read. Time a week before labeling any comment in it.

```text
uv run afterword label --run <run-id> --mode chronological --week <any date in the week>
```

- Read as you would in an ordinary review: each comment, its reply chain, then Enter.
- At the end the tool asks `Record this as a valid timing? (y/n)`. Answer `y` only if the read was a real review, start to finish. If the average is under 2 seconds per comment, it warns before asking.
- Anything other than `y` (including `q` or closing the input) saves the run under `reports/timing/practice/`.
- A historical week can be measured validly only once. Every read of a week, practice included, makes later timings of it a weaker lower bound. Record how many times a week was read before its valid timing.

Weeks to time (both timed and recorded as valid on 2026-10-03, from run `20261003T141450Z`; results in `CLAIMS.md`, C-009, 2026-10-04):

- **Typical: 2026-07-27 to 2026-08-02 (7 comments from others).** This replaces 2026-09-21, the week the C-009 baseline first named, which had been re-read twice by 2026-10-03 (once in a practice timing run that was nearly recorded as evidence). It is the complete week closest to the trailing-13-week median (7) of run `20261002T171152Z`, excluding the two weeks already chosen. To recompute: `uv run afterword baseline --run <run-id> --exclude-week 2026-09-21 --exclude-week 2026-09-07`.
- **Busy: 2026-09-07 to 2026-09-13 (44).**

Before its valid timing, neither week was to be read on DEV, in practice, or in a labeling batch. Both timings are done, so the weeks can now be labeled like any other.

## 3. Labeling sessions

Two tools label the same batches and write the same records: `afterword label` in the terminal and `afterword label-ui` in a local browser page. Either can continue where the other stopped.

```text
uv run afterword label-ui --run <run-id>
uv run afterword label --run <run-id>
```

### Which tool

- **`label-ui`** for labeling. It is faster: one screen per comment, the thread beside the form, single keys for every choice, and nothing to retype.
- **`label`** for chronological timing (`--mode chronological` exists only there), and for labeling when no browser is available or a session is run over SSH.
- Never run both at the same time on the same pass. Each reads which comments are done when its batch starts, so two tools running at once could label the same comment twice.

### Launching `label-ui`

```text
uv run afterword label-ui --run <run-id>
uv run afterword label-ui --run <run-id> --posts random --seed 7
uv run afterword label-ui --run <run-id> --port 8800 --no-browser
```

The terminal prints the run's counts (comments to label and those excluded), the batch, and one line:

```text
open: http://127.0.0.1:8765/?t=<token>
```

Your browser opens that URL. With `--no-browser`, or if it does not open, copy the whole URL, including `?t=` and the token, into the browser. The token is new for every launch, so an old URL stops working; the page refuses any request without it. The server listens on `127.0.0.1` only. The port is 8765 unless `--port` names another (`--port 0` picks a free one). The terminal never shows comment text.

The options are those of `afterword label`: `--batch-size`, `--pass`, `--corpus-version`, `--set`, `--ids`, `--posts`, and `--seed`.

### The screen

- **Left:** the post title, when the comment was posted, the context status, and the thread as it stood when the comment was posted (later comments hidden). The context status says whether any known gap exists (a deleted earlier comment, a post edited after the comment), whether the comment replies to you (`REPLY_TO_AUTHOR` is then set automatically), and whether your reply already exists in the snapshot (`replied_before_labeling`). By default only the reply chain is shown; `t` shows every earlier comment in the thread.
- **Right:** the class (radio buttons), flags (checkboxes), the prospective grade, the retrospective grade (shown only after the prospective grade is set), the reason, a hard-to-label note, and the shortcut legend. Hovering a class or flag shows its definition; `h` shows all of them.
- **Header:** pass, batch, position in the batch, labels saved this session, and comments still unlabeled in the pass. A badge on the right shows the totals for the run: comments labeled (initial pass), relabeled (calibration pass), and eligible. It never shows classes or grades.

### Keyboard shortcuts

| Key | Action |
| --- | --- |
| `1` to `9`, `0` | Class, in TAXONOMY.md precedence order (`0` is `UNCERTAIN`) |
| `n` | `NEEDS_THREAD_CONTEXT` |
| `c` | `CONTAINS_CODE` |
| `l` | `CONTAINS_LINK` |
| `r` | `REFERENCES_SPECIFIC_CLAIM` |
| `o` | `ADDRESSED_TO_OTHER_COMMENTER` |
| `x` | `HOSTILE_TONE` |
| `i` | `POSSIBLE_INSTRUCTION_TEXT` |
| Shift+`0` to Shift+`3` | Prospective grade |
| `g` then `0` to `3` | Retrospective grade (`g` then `-` clears it) |
| `e` | Type the reason |
| `w` | Type a hard-to-label note |
| Esc | Leave a text field; close the definitions |
| Enter | Save the label and show the next comment (also from inside a text field) |
| `t` | Toggle the reply chain and the full thread as of the comment |
| `h` or `?` | Show or hide every class and flag with its definition |
| `s` | Skip this comment without a label (a typed note is kept) |
| `q` | Stop the session (asks to confirm while a comment is open) |
| `b` | After a batch: start the next batch |

Flag keys toggle. Every key except Enter and Esc is ignored while typing in a text field. A label is saved only when it has a class and a prospective grade, plus a reason for a grade of 2 or 3; otherwise the page says what is missing.

### Resuming and stopping

- **Every Enter writes the label at once.** Nothing is lost when the session stops, the tab closes, or the process ends, except the comment on screen.
- **Resuming** is running the same command again: the next batch starts with the first unlabeled comment. A skipped comment has no label, so it comes back in a later batch. With `--posts random`, use the same `--seed` for the whole pass to keep the same order; the seed is recorded in each batch record. Comments within a post are oldest first whatever the order.
- **Between batches** the page shows a summary with "Start next batch (b)" and "Stop (q)". Starting the next batch is the same as running the command again, so the rule still holds: stop when attention drops.
- **Stopping the server:** press `q` in the page (or the Stop button), or Ctrl+C in the terminal. Either closes an unfinished batch as `quit` and ends the process; the terminal prints how many labels were saved. Closing the tab does not stop the server. Reopening the same URL returns to the same comment, but the labeling time for that comment keeps running meanwhile, so stop rather than leave a comment open.

### Saving and stopping in the terminal (`label`)

- A label is written when its summary is confirmed at the `Save? [Enter = yes, r = redo, s = skip, q = save and stop]` prompt: Enter saves; `q` (or end of input) saves, then stops. Each saved label is on disk before the next comment is shown.
- `q` at any earlier prompt, or Ctrl+C anywhere, stops without saving the comment on screen. The tool says so: "was NOT saved" when answers had been entered for it, "was not labeled" when none had. The batch's end record carries `abandoned_in_progress` (true when answers were discarded). The comment comes back in a later batch.
- When a batch ends, by completion or by `q`, the last line gives the totals: "N labeled this session, bringing the total to M of T." M counts the eligible comments labeled in the pass and T the eligible comments in the run, by the same rules the tools use to choose batches.

### Progress

```text
uv run afterword label status --run <run-id>
```

Prints, for the run and corpus version: eligible comments, labeled and remaining (initial pass), labeled comments by pass, labels by tool (`terminal`, `browser`, or `not recorded` for batches from before 2026-10-04, when the tool started being recorded), and any labeled comment no longer eligible in the run. Counts only: no classes, grades, IDs, or text. Progress while labeling is always totals only, so a running distribution cannot steer the next label.

### Calibration pass

```text
uv run afterword label-ui --run <run-id> --pass calibration --ids <file>
```

Re-labels comments that already have an initial label, from scratch, with the earlier label hidden. Without `--ids` it offers every labeled comment, in the usual order, so the earliest come first. Calibration labels go to their own file and never overwrite anything; which label analysis uses is defined in `LABELING-GUIDE.md`. Do not look at the earlier labels before or during a calibration batch.

### Rules that apply to both tools

- One batch is at most 40 comments (`LABELING-GUIDE.md`). Saved labels survive stopping at any point.
- Stop between batches when attention drops. Fatigue drift is the reason for the limit, so do not run batches back to back to beat it.
- Comments come post by post, oldest first within a post. `--posts random --seed N` shuffles the order of posts, not of comments within a post. Do not skip ahead in the thread on DEV while labeling.
- Do not look at earlier labels, the commenter's profile, or any classifier output.
- Write hard-to-label notes when they come up (the note field, or the prompt in the terminal). They are candidates for the adversarial set and for taxonomy revision.
- Self-agreement: at least 14 days after the initial pass, with `--pass self_agreement --ids <file>` (`LABELING-GUIDE.md`).

## 4. The prospective period

The test period starts at the preregistration commit (ADR-010) and runs until the stopping rule: both 20 consequential and 100 total test comments, or 16 weeks. The routine, once a week:

1. **Probe:** a fresh full run.
2. **Shadow mode:** run B1 and B2 on the new test comments, write their outputs to a git-ignored file, and commit its SHA-256. Nothing is shown. (Stage 3; not built yet.)
3. **Time (optional, first read):** time the week's comments with `--mode chronological` before reading them anywhere else. A test-period timing is a first-read measurement, unlike the historical re-reads.
4. **Label:** label the new test comments with `--set test`, at first read where possible.
5. **Reply:** only after labeling, where possible. A reply written first is recorded as `replied_before_labeling` and may carry hindsight into the prospective grade.

Practical rules for the period:

- Label weekly. A missed week delays labels but does not unblind anything; do not catch up by labeling after reading replies.
- Reading a notification on DEV is a first read. Where you can, leave new comments unread until the weekly session.
- Comments arriving on posts published before preregistration belong to neither set. They are counted, not labeled as `test`.

Not built yet, needed before preregistration: `afterword label` cannot yet restrict a batch to test comments (posts published after the preregistration commit). Until it can, `--set test` must not be used.
