# Workflow

**Version:** 1 (2026-10-02)

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

Weeks to time:

- **Typical: 2026-07-27 to 2026-08-02 (7 comments from others).** This replaces 2026-09-21, the week the C-009 baseline first named, which had been re-read twice by 2026-10-03 (once in a practice timing run that was nearly recorded as evidence). It is the complete week closest to the trailing-13-week median (7) of run `20261002T171152Z`, excluding the two weeks already chosen. To recompute: `uv run afterword baseline --run <run-id> --exclude-week 2026-09-21 --exclude-week 2026-09-07`.
- **Busy: 2026-09-07 to 2026-09-13 (44).**

Do not read either week on DEV, in practice, or in a labeling batch before its valid timing.

## 3. Labeling sessions

```text
uv run afterword label --run <run-id>
```

- One batch is at most 40 comments (`LABELING-GUIDE.md`). The tool labels one batch and stops; run it again for the next. Saved labels survive `q`.
- Stop between batches when attention drops. Fatigue drift is the reason for the limit, so do not run batches back to back to beat it.
- Comments come post by post, oldest first within a post. Do not skip ahead in the thread on DEV while labeling.
- Do not look at earlier labels, the commenter's profile, or any classifier output (none exists yet).
- Write hard-to-label notes at the prompt. They are candidates for the adversarial set and for taxonomy revision.
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
