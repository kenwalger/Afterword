## Self-Agreement Process - 23 October 2026

Prompt:

```text
Diagnosis only; change nothing. The self-agreement report
(reports/eval/self-agreement-report-20261023T181941Z.json) shows
consequential agreement 53 of 80, with 26 comments dropping out of
consequential and 1 entering; class kappa 0.344.

Report, counts only (no text, no IDs on screen):
1. The 26 downgrades by original prospective grade -> new grade (for
   example 2->1, 3->1, 2->0).
2. Agreement split by the original labels' pass and order: publication
   order versus shuffled, and by labeling date.
3. Agreement split by original class, and the class transitions with
   the largest counts.
4. Whether the self-agreement labels were made in one sitting (batch
   records and durations), and any sign of fatigue across the session
   (grade distribution by position in the session).
5. If the original grades were replaced by the self-agreement standard,
   what share of the 80 would be consequential, and a rough projection
   for the full dev set.
6. Options, with effort estimates: (a) re-grade only the consequential
   field on labels originally graded 2 or 3; (b) relabel the early
   labels fully; (c) relabel all of dev. Recommend nothing; set out the
   trade-offs.

Record this in the friction logs and append a dated entry to C-001 and
C-011 (the drift claim). Do not commit.
```

Output:

```text
The diagnosis is done. Everything below is counts from afterword.label_records; no comment text or IDs were read or printed. No code, label or report file changed. One thing first: the report covers 80 of the 112 comments drawn. The two self-agreement batches went through posts in publication order, so
  the oldest labels were done first. The 32 left unlabeled are all from the shuffled pass: 23 labeled under lg-v0.3 and 9 under lg-v0.6, and 26 of them were graded 2 or 3. The report doesn't say this; only the draw record does.

  1. The 26 downgrades: 2→1: 21, 3→1: 3, 2→0: 1, 3→0: 1. Of the 66 originally graded 2 or 3, 40 stayed at 2 or 3 (60.6%, Wilson 48.5% to 71.5%). The one upgrade was 1→2, out of 14 comments originally graded 0 or 1.
  - In 10 of the 26, the original label's own retrospective grade was already below 2.
  - Comments with no author reply yet when first labeled were downgraded more often: 11 of 15, against 15 of 51 with a reply.
  
  2. By pass, order and date: all 80 originals are from the initial pass.

  ┌────────────────────────────┬──────────────────────────┬────────────────┐
  │      Original labels       │ Same consequential split │ Kept at 2 or 3 │
  ├────────────────────────────┼──────────────────────────┼────────────────┤
  │ Publication order, lg-v0.2 │ 35 of 50                 │ 25 of 39       │
  ├────────────────────────────┼──────────────────────────┼────────────────┤
  │ Shuffled, lg-v0.3          │ 16 of 27                 │ 14 of 25       │
  ├────────────────────────────┼──────────────────────────┼────────────────┤
  │ Shuffled, lg-v0.6          │ 2 of 3                   │ 1 of 2         │
  └────────────────────────────┴──────────────────────────┴────────────────┘

  By labeling date: 10-03: 5/5, 10-04: 30/45, 10-05: 1/1, 10-07: 15/26, 10-09: 2/3.

  3. By class:
  - TECHNICAL_EXTENSION (40 originals): 8 kept the same class, 22 the same split, 18 were downgraded.
  - TECHNICAL_QUESTION (21): 18 kept the class, 18 the split.
  - CONVERSATIONAL (11): 9 kept the class, 8 the split.
  - 42 comments changed class. The biggest moves are TECHNICAL_EXTENSION → CONVERSATIONAL (18), → TECHNICAL_QUESTION (6) and → CHALLENGE_OR_COUNTEREXAMPLE (4).
  - 14 of the 26 downgrades are extension → conversational. That is the boundary the 2026-10-18 relabeling proposal flagged as easy to confuse, and the one the planned extension split (candidate (b)) would cut.

  4. Sitting and fatigue: it was one sitting.
  - Two browser batches of 40: 38.6 minutes, then 15.8 minutes, 17 seconds apart. No skips and no notes.
  - Time per label was a median of 25 s, against 42 s for the originals of the same comments. By quarter of the sitting the median fell: 43, 30, 29, 17 s.
  - Downgrades per quarter were 2, 9, 6, 9. Position is mixed up with which original batch a comment came from, but within each batch the second half still downgraded more: 4 of 19 then 10 of 20, and 4 of 12 then 7 of 13. I can't separate fatigue from later posts.

  5. If the new grades replaced the originals:
  - In the 80, consequential falls from 66 (82.5%) to 41 (51.3%). The sample over-represents graded comments, so this isn't a corpus share.
  - Reweighted to the pool of 342 labels old enough to draw from: 26.9% → about 21.5%.
  - Full dev set: about 103 of 478 (21.6%) against 129 (27.0%). That is about 78 kept (range 63 to 92) plus about 25 upgrades. The upgrade figure rests on 1 of 14, so it is very uncertain.
  - The lg-v0.6 labels hold 45 of the 129 consequential and are almost unmeasured.

  6. Options: effort uses this sitting's pace (41 s per label) and the originals' pace (77 s) as low and high.
  - Before any of them: labeling the 32 remaining comments of the draw takes 22 to 41 minutes and completes the check as drawn.
  - (a) Re-grade only the consequential field on labels graded 2 or 3: 129 labels, about 90 minutes (about 45 for the 63 not yet re-graded).
    - It needs a new grade-only pass: code, tests and a guide version bump, which also means reviewing LABELING-FIELD-GUIDE.md.
    - Grades can only go down; the 349 graded 0 or 1 are never re-read.
    - Every comment shown was graded 2 or 3, which is itself a cue to the labeler.
    - Class stays as it was, and class is where most of the disagreement is.
  - (b) Fully relabel the 302 early labels (10-03 to 10-07): 3.4 to 6.5 hours, 8 batches.
    - This group contains 25 of the 26 downgrades.
    - 77 of today's 80 would be read a third time within days.
    - The 176 lg-v0.6 labels stay as they are, and they are unmeasured.
  - (c) Relabel all 478: 5.4 to 10.2 hours, 12 batches. Every label ends up under one guide version and one period. This is closest to the guide's own wording: "relabeled as a new version under a revised guide".
  - Shared by all three:
    - The guide doesn't define "poor" agreement.
    - Neither read is known to be the right one; the relabel was faster and downgraded more late in the sitting.
    - The guide says original labels aren't changed after this check, so any relabel writes new records. A "new version" would also have to fit the 2026-10-18 decision to keep every label in unfrozen.
    - A recheck of the new labels needs another 14 days, which moves preregistration.
    - Every dev result gets recomputed. Model outputs are cached, so rescoring is cheap; the labeling isn't.
  - Doing nothing is also open: report the 66.3% agreement as a finding.

  I wrote these files (not committed):
  - friction-delight-logs/session13.md: session notes
  - docs/friction-log/session-13.md: public log
  - docs/FRICTION-LOG.md: new index row
  - docs/CLAIMS.md: 2026-10-23 entries on C-001 and C-011
  - commit-message.txt: the commit message

  The C-011 entry notes that a 14-day baseline this low makes its falsifier easier to meet by default. All four edited docs are free of em-dashes, and the identity scan passed.

```