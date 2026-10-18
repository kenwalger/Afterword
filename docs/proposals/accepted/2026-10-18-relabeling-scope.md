# Proposal: relabeling scope, and the self-agreement check

**Status:** DECIDED by the author, 2026-10-18 (session 11): **the self-agreement check runs on or after 2026-10-22, by the same rule** (pool: analysis labels at least 14 days old when the list is drawn; every pooled comment graded 2 or 3 plus 25 at random, seed 20261018). The 44-ID list prepared on 2026-10-18 is superseded and is not used. **The calibration pass on the first 150 is dropped** unless the self-agreement check shows a problem: under `pp-v0.2` none of those labels' tiers depends on the flags the pass was meant to correct, and the C-010 outlier is not in them. The text below is the proposal as submitted.

**Basis:** all 478 `dev` labels (478 initial, 0 calibration, 0 self-agreement), the candidates in `docs/proposals/accepted/2026-10-18-adopt-pp-v0.2.md` and `docs/proposals/accepted/2026-10-18-consequence-to-tier.md`. Counts only.

## Which labels would change a result if relabeled

A label enters the five primary measures in two ways: the **grade** (consequential or not) for every condition, and the **class and flags** for the oracle only. A classifier's review reduction and `SURFACE` size do not depend on labels at all.

| Part of a label | What it can change | Labels where a change would matter (all 478) |
| --- | --- | --- |
| Grade, comment a condition collapses | recall | B1 collapses 79: 11 graded 1 and 3 graded 2 sit at the 1/2 boundary. Llama (`pp-v0.2`) collapses 39: 5 graded 1, none graded 2. |
| Grade, comment a condition puts at `SURFACE` | SURFACE precision and capture | B1: 83 graded 1, 62 graded 2. Llama: 86 graded 1, 59 graded 2. |
| Grade, comment at `QUEUE` | capture's denominator only | B1: 97 graded 1, 35 graded 2. Llama: 100 and 41. |
| Class, oracle | the oracle's tier, hence every ceiling | 404 of 478 have a confusable class with a different default tier (the boundaries in `LABELING-FIELD-GUIDE.md`: acknowledgment and conversational, spam and extension, question classes, challenge and extension). |
| `REFERENCES_SPECIFIC_CLAIM`, `NEEDS_THREAD_CONTEXT` | the oracle's tier under `pp-v0.1` only; flag precision (secondary) always | under `pp-v0.1`, 1 label's tier depends on one of them (graded below 2); under `pp-v0.2`, none. |
| `TECHNICAL_EXTENSION` split (candidate (b)) | the split's oracle, if adopted | all 131 labeled extensions; no existing label carries it. |

Grades at the 1/2 boundary are the labels whose relabeling most often changes a reported number: 291 of 478 are graded 1 or 2 (191 and 100). Which of them actually flip is what the self-agreement check estimates.

## The calibration pass on the first 150, if `pp-v0.2` is adopted

The calibration list (`reports/eval/calibration-first150.txt`, 150 IDs, git-ignored) is the 150 publication-order labels, made under `lg-v0.2` and `tax-v0.1`. The pass was planned because `tax-v0.1` applied `REFERENCES_SPECIFIC_CLAIM` broadly (82 of 150), and because the first labels were the labeler's least practiced (`docs/friction-log/session-7.md`).

- **The flag motive is gone under `pp-v0.2`.** No first-150 label's oracle tier depends on its `REFERENCES_SPECIFIC_CLAIM` or `NEEDS_THREAD_CONTEXT` (0 of 150; under `pp-v0.1`, 1, graded below 2). Relabeling the 82 flags would change only `REFERENCES_SPECIFIC_CLAIM` flag precision, a secondary measure already reported apart by taxonomy version.
- **The C-010 motive is gone.** Session 8 hoped the pass would say whether the publication-order and shuffled labels differ in hindsight agreement because of the labeler or the sample. With all labels, the outlier is the first 152 shuffled labels (`lg-v0.3`), not the first 150: the next 176 agree with hindsight as often as the first 150 (95.3% against 95.2%; `EVALUATION.md` v16). Relabeling the first 150 cannot explain a difference they are not part of.
- **What still matters in the first 150:** class and grade, as for any label. 120 of the 150 sit in a class with a confusable neighbor of another default tier, and 92 are graded 1 or 2. Those are worth redoing only if the early labels are believed less reliable than the later ones, and the self-agreement check is the measurement of that.

**So under `pp-v0.2`, little of the calibration pass still matters by design.** What it would still buy is fresher class and grade judgments on the earliest labels; whether they need it is better decided after the self-agreement check, which measures it, than assumed.

## Order: self-agreement before any calibration or split relabel

- **The self-agreement check measures the labels analysis uses.** A calibration label replaces the analysis label and restarts the 14-day clock for that comment (`LABELING-GUIDE.md`), so calibrating first would push the check back two weeks for every comment calibrated.
- **Each reread contaminates the next.** All 44 comments in the self-agreement sample are in the first 150 (below). Calibrating them afterwards would be a third read; relabeling the 131 extensions for candidate (b) would reread the 17 extensions among them.
- **Proposed order:** self-agreement check now; then decide, from its result, whether a calibration pass is needed at all, and whether candidate (b)'s relabel goes ahead.

## The self-agreement check, prepared

`LABELING-GUIDE.md`: at least 14 days after the initial labels, re-label a random sample of 25 comments plus every comment originally graded 2 or 3, without looking at the originals; report Cohen's kappa on class, and raw agreement on the consequential binary with every disagreement listed. The guide's text says "from the test set"; here it is applied to `dev`, as the author asked.

- **Pool:** analysis labels made at least 14 days before 2026-10-18 19:19 UTC: **107**, all in publication order (labeled 2026-10-03 and 2026-10-04, up to 17:22 UTC). Labels made after that are not yet 14 days old.
- **Sample:** every pooled comment graded 2 or 3 (21), plus 25 drawn at random from the whole pool (seed 20261018; 2 of them are also graded 2 or 3): **44 comments** on 12 posts, all `lg-v0.2` and `tax-v0.1` labels.
- **File:** `reports/eval/self-agreement-20261018-s20261018.txt` (git-ignored; 44 IDs, one per line).
- **Command** (author's terminal; two batches, since a batch is at most 40):

  ```text
  uv run afterword label-ui --run 20261018T173927Z --pass self_agreement --ids reports/eval/self-agreement-20261018-s20261018.txt
  ```

  Run it again for the second batch. Labels go to `fixtures/labels/unfrozen/self_agreement.jsonl` and never replace anything.

**A choice for the author: run it now, or wait four days.** The sample is all early, publication-order labels, because only those are old enough. From 2026-10-22 the 152 shuffled labels of 2026-10-04 to 2026-10-07 also qualify, and they are the group whose hindsight agreement stands out (C-010). A list drawn by the same rule at the same hour on 2026-10-22 would pool all 302 labels of the first two parts and hold 104 comments (84 graded 2 or 3, plus 25 random, of which 5 overlap): three batches. Now is smaller and sooner; later covers the group in question. The list can be redrawn by the same rule on any date.

**Not built yet:** a counts-only comparison of self-agreement labels with the originals (kappa on class, the binary with its disagreements). `afterword.label_records.calibration_differences` does the same for calibration labels; a sibling for self-agreement is a small addition, needed after the labels exist, not before.

## Decision requested

1. Run the self-agreement check now (44) or from 2026-10-22 (104).
2. Whether the calibration pass on the first 150 is still wanted, after the check.
3. If candidate (b) goes ahead, its 131-extension relabel comes after the check.
