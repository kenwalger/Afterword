# Proposal: registered thresholds, the frozen versions, and the preregistration record

**Status:** ACCEPTED by the author, 2026-10-26 (session 15). Decisions: Decision 1 (a), thresholds relative to the oracle on the test set; Decision 2, the recommended rules for recall, review reduction (0.50), SURFACE size (both parts), and SURFACE capture (1.0), and "Both" for SURFACE precision (at least 0.50 times the oracle's precision and a lift of at least 1.25); Decision 3, the recommended rule, (a) or (b), with option (c) reported descriptively and not registered; Decision 4, Part 1 publishes after the seal, so `excluded_posts` starts empty and Part 1 is excluded by amendment once published; the application version is bumped to `0.2.0` (in the preregistration commit, as decided; moved by the author on 2026-10-27 into a preparation commit before the seal, when the seal moved to early November and Part 1 to 2026-11-10). Written into `EVALUATION.md` v22 ("Registered thresholds", "Frozen versions"). The text below is the proposal as submitted, except Decision 4 and the sections on the application version and the record, updated at the author's request to the order decided (seal first, then Part 1) and to the `afterword preregistration write` command.

**Date and basis:** all 494 `dev` labels in run `20261026T181641Z` (every comment from others; one labeled comment since deleted upstream and purged is not scored), the analysis label per comment (the latest from any pass other than `self_agreement`), 150 of them calibration labels under `lg-v0.7`. B1 `hb-v0.2` and Llama (`llama3.1:8b-instruct-q4_K_M`, `pr-v0.2`, `num_ctx=4096`, digest `46e0c10c039e...`) from the classification cache, every one of the 494 classified `OK`; policy `pp-v0.2`. Scored offline (`afterword evaluate`, reports `reports/eval/20261026T214645Z-b1-hb-v0.2-pp-v0.2.json` and `20261026T214646Z-b2-llama3.1_8b-instruct-q4_K_M-pp-v0.2.json`, git-ignored). No model ran in the session.

This is development evidence: historical comments, labels made with hindsight (298 of 494 after the author's reply), the policy and B1's threshold tuned on the same set.

## The question each threshold answers

`PREREGISTRATION.md` asks the author one question per number: "If the test came back exactly at this number, would I call that a success?" The dev evidence below says where the two conditions are likely to land, not where the bar should be. A threshold chosen so that dev passes is tuning on the result; a threshold chosen for what success means, with dev used only to say what to expect, is a preregistration.

## The dev evidence

### All 494 labels

| | B1 `hb-v0.2` | Llama (B2) | Oracle (labels, class and flags) |
| --- | --- | --- | --- |
| Consequential recall | 155 of 158 (3 missed) | 157 of 158 (1 missed) | 157 of 158 (1 missed) |
| Review reduction | 79 of 494 (16.0%; 13.0 to 19.5) | 39 (7.9%; 5.8 to 10.6) | 118 (23.9%; 20.3 to 27.8) |
| SURFACE size | 210 (42.5%) | 229 (46.4%) | 110 (22.3%) |
| SURFACE precision | 95 of 210 (45.2%; 38.7 to 52.0) | 105 of 229 (45.9%; 39.5 to 52.3) | 88 of 110 (80.0%; 71.6 to 86.4) |
| SURFACE capture | 95 of 158 (60.1%; 52.3 to 67.4) | 105 of 158 (66.5%; 58.8 to 73.3) | 88 of 158 (55.7%; 47.9 to 63.2) |

### The 167 labels made under `lg-v0.7` (the guide the test set will be labeled under)

150 calibration labels (publication order) and the 17 comments labeled since 2026-10-19 (shuffled order). This slice is the closest `dev` analogue to the test set's labeling, and small.

| | B1 | Llama | Oracle |
| --- | --- | --- | --- |
| Consequential | 69 of 167 (41.3%) | | |
| Missed | 2 | 1 | 1 |
| Review reduction | 25 (15.0%) | 17 (10.2%) | 37 (22.2%) |
| SURFACE size | 75 (44.9%) | 85 (50.9%) | 55 (32.9%) |
| SURFACE precision | 46 of 75 (61.3%) | 54 of 85 (63.5%) | 51 of 55 (92.7%) |
| SURFACE capture | 46 of 69 (66.7%) | 54 of 69 (78.3%) | 51 of 69 (73.9%) |

### Each condition relative to the oracle

| Ratio to the oracle | B1, all 494 | Llama, all 494 | B1, `lg-v0.7` | Llama, `lg-v0.7` |
| --- | --- | --- | --- | --- |
| Review reduction (collapsed / oracle collapsed) | 0.67 | 0.33 | 0.68 | 0.46 |
| SURFACE size (size / oracle size) | 1.91 | 2.08 | 1.36 | 1.55 |
| SURFACE precision (share / oracle share) | 0.57 | 0.57 | 0.66 | 0.69 |
| SURFACE capture (share / oracle share) | 1.08 | 1.19 | 0.90 | 1.06 |
| SURFACE precision / consequential share ("lift") | 1.41 | 1.43 | 1.48 | 1.54 |

**What the evidence says about the oracle as a reference.** The guide changed the oracle. Under `lg-v0.7` the consequential share is 41.3% against 25.6% to 29.1% in the older labels, and the oracle's `SURFACE` is a third of comments, not a fifth, because the relabel moved comments into `CHALLENGE_OR_COUNTEREXAMPLE` and `TECHNICAL_QUESTION` (both `SURFACE` classes) and out of `TECHNICAL_EXTENSION`. An oracle number fixed from the mixed `dev` set would compare test results with a ceiling labeled under other guides.

## Decision 1: what the thresholds are relative to

- **(a) Recommended: the oracle on the test set.** Each threshold is a ratio to the oracle computed from the test labels themselves under `pp-v0.2`, at scoring time. The oracle uses labels only, no classifier output, so it reveals nothing during accrual, and it is computed from the same labels the conditions are scored against: same guide, same posts, same mix. The `dev` ratios above become the expectation, not the bar.
- **(b) The oracle on `dev`, as numbers.** Each threshold is a fixed number taken from the `dev` oracle (for example "review reduction at least 12% of test comments"). Simple to read; but the `dev` oracle mixes three guide versions, and the test set's class mix is unknown.

`EVALUATION.md` ("SURFACE size, SURFACE precision, and SURFACE capture") says a SURFACE threshold is registered "relative to the oracle on `dev`". Option (a) changes that wording: nothing is registered yet, so it is the author's to change, and the change would be recorded in `EVALUATION.md` with the thresholds.

## Decision 2: the five thresholds (B2 success, C-002)

A condition is judged on all five at once (`EVALUATION.md`). B2 meets the registered result when it meets all five; B1 is reported against the same thresholds. Every result is reported as counts first, with Wilson intervals, whether or not a threshold is met, and with the stopping rule's caveat (a measure resting on fewer than 20 consequential or 100 comments is indicative).

For each measure: a recommended value, alternatives, and what `dev` gives (all 494 / the `lg-v0.7` slice). "Pass" on `dev` is information, not a reason.

### 1. Consequential recall

| Option | Rule | B1 | Llama |
| --- | --- | --- | --- |
| **Recommended** | Collapsed consequential comments at most 1 per 20 consequential test comments, rounded down, and never fewer than 1 allowed (20 to 39 consequential: at most 1; 40 to 59: at most 2) | pass / pass | pass / pass |
| Strict | No consequential comment collapsed | fail / fail | fail / fail |
| Oracle-relative | Collapsed consequential at most the oracle's own collapsed consequential plus 1 | fail (3 against 2) / pass | pass / pass |

Why the recommended form: with 20 to 40 consequential test comments, one miss is 2.5 to 5 points of recall, so a percentage threshold would be decided by a single comment either way. The count says it directly. The strict option fails on `dev` for both, including Llama, because the oracle itself collapses one consequential comment (labeled as an acknowledgment, graded 2): perfect classification cannot meet it. Design preference stands: extra false positives are tolerated before consequential misses, which is why recall is a count of misses and the others are ratios.

### 2. Review reduction

| Option | Rule (collapsed / oracle collapsed) | B1 | Llama |
| --- | --- | --- | --- |
| **Recommended** | At least 0.50 | pass / pass | fail (0.33) / fail (0.46) |
| Lower | At least 0.33 | pass / pass | fail by one comment (39 against 39.3) / pass |
| Lowest | At least 0.25 | pass / pass | pass / pass |

Why 0.50: the claim (C-002) is falsified when "review savings are trivial". Collapsing half of what perfect classification would collapse is the smallest saving that is plainly not trivial on a set where the ceiling itself is about a quarter of comments. Recommending it means recommending a bar that `dev` predicts Llama will miss, and B1 will meet. That is a real possibility of the test, and registering a lower bar because Llama is the chosen B2 would be choosing the threshold to fit the model.

### 3. SURFACE size

| Option | Rule | B1 | Llama |
| --- | --- | --- | --- |
| **Recommended** | At most 2.0 times the oracle's SURFACE, and at most half of all test comments | pass / pass | fail (2.08) / fail (50.9% of comments) |
| Looser | At most 2.0 times the oracle's SURFACE | pass / pass | fail (2.08) / pass |
| Absolute only | At most half of all test comments | pass / pass | pass (46.4%) / fail (50.9%) |

Why both parts: the ratio keeps "review first" within reach of what perfect classes would surface; the absolute cap keeps it a minority of comments, so the phrase still means something whatever the oracle does.

### 4. SURFACE precision

| Option | Rule | B1 | Llama |
| --- | --- | --- | --- |
| **Recommended** | At least 0.50 times the oracle's precision | pass (0.57) / pass (0.66) | pass (0.57) / pass (0.69) |
| Lift | At least 1.25 times the test set's consequential share | pass / pass | pass / pass |
| Both | Both of the above | pass / pass | pass / pass |

Lift says whether `SURFACE` is richer in consequential comments than the stream as a whole; a condition with lift near 1 has made "review first" a random sample. Either form passes on `dev` for both; they differ on a test set whose consequential share or oracle precision moves.

### 5. SURFACE capture

| Option | Rule | B1 | Llama |
| --- | --- | --- | --- |
| **Recommended** | At least 1.0 times the oracle's capture | pass (1.08) / fail (0.90) | pass (1.19) / pass (1.06) |
| Looser | At least 0.90 times the oracle's capture | pass / pass | pass / pass |

Capture is the one measure where a condition can beat the oracle, by surfacing more. The SURFACE size threshold is what stops that from being bought with an oversized `SURFACE`; the two only mean something together, which is why all five are judged at once.

## Decision 3: B2 meaningfully beats B1 (C-008)

The claim, unchanged: B2 achieves "materially better consequential recall at the same review reduction, or better reduction at the same recall", and is weakened if "B1 matches B2 within one or two consequential comments". The rule should make those words checkable, not change them.

**Recommended rule.** B2 meaningfully beats B1 on the test set if either:

- **(a) Recall.** B2 collapses at least 3 fewer consequential comments than B1, and B2's collapsed count is no more than 5% of test comments below B1's ("the same review reduction"); or
- **(b) Reduction.** B2 collapses more comments than B1 by at least 5% of test comments, and B2 collapses no more consequential comments than B1 ("the same recall").

Otherwise B1 and B2 are reported as not meaningfully different on the claim's terms, with all five measures for both.

- On `dev` (all 494): (a) fails, B2 collapses 2 fewer consequential (1 against 3) and 40 fewer comments (8.1% of 494); (b) fails. On the `lg-v0.7` slice, the same (1 against 2; 8 fewer collapses, 4.8%).
- **Why 3:** the falsifier says "within one or two"; 3 is the smallest difference outside it. With 20 to 40 consequential test comments and B1 missing about 2% of them on `dev`, a difference of 3 is unlikely, so this rule is likely to report no meaningful difference. That is a valid result (`EVALUATION.md`: "If B1 is close to B2, that is a reportable result").
- **Why 5% for "the same":** one tolerance for both directions, about 5 to 8 comments on a test set of 100 to 150.

**Optional (c), a SURFACE route, not in the claim's text.** B2 places at least 3 more consequential comments at `SURFACE` than B1, with a `SURFACE` no more than 10% larger. On `dev`: all 494, 10 more (105 against 95) with a 9.0% larger `SURFACE`, pass; `lg-v0.7` slice, 8 more with 13.3% larger, fail. SURFACE measures are co-primary since 2026-10-08, but C-008 names recall and reduction. Adding (c) would widen what counts as the model adding value; if the author wants it, record it as a registered reading of C-008 in the claim's ledger, dated, without editing the claim. If not, (c) is reported descriptively.

Also reported, not registered as a test: the paired counts (consequential comments one condition surfaces and the other collapses, each way), since both run on the same comments. On `dev`: of the consequential comments, B1 and Llama put 67 at `SURFACE` together, 38 only Llama, 28 only B1; their misses do not overlap (B1's 3, Llama's 1, the oracle's 1 are five different comments).

## Decision 4: posts about Afterword

**Registered rule (unchanged from ADR-010):** a post about Afterword itself is excluded from the test set; posts known at preregistration are listed in `excluded_posts` then, later ones by a recorded amendment before any of their comments is labeled.

**Posts that are about Afterword, by ID:** none as of run `20261026T181641Z`, so `excluded_posts` starts empty.

**Decided (the author, 2026-10-26): the seal comes first, then Part 1.** Part 1 (scheduled 2026-11-10, after the seal in early November; first scheduled 2026-10-27) is published after `registered_at`, so it is a test-period post. It is excluded by a recorded amendment once published, before any of its comments is labeled (`afterword preregistration posts` for its ID, then `afterword preregistration exclude-post --post <id>`, commit, push). Its comments then belong to neither set, so none of them enters `dev` or the frozen corpus. This settles the question the draft raised (whether Part 1's early comments would join `dev`) without amending ADR-010. Parts 2 and 3 follow the same path.

## The freeze: versions recorded at preregistration

| Item | Frozen as | Where it lives |
| --- | --- | --- |
| Taxonomy | `tax-v0.2` | `TAXONOMY.md`; `afterword.taxonomy.TAXONOMY_VERSION` |
| Labeling guide | `lg-v0.7` | `LABELING-GUIDE.md`; `afterword.labeling.LABEL_GUIDE_VERSION` |
| Labeling field guide | v5 | `LABELING-FIELD-GUIDE.md` |
| Normalization | `norm-v0.1` | `afterword.normalize.NORMALIZATION_VERSION` |
| Pre-check | `pc-v0.1`, with adv-109 and adv-110 as registered known limitations | `afterword.precheck.PRECHECK_VERSION` |
| Priority policy | `pp-v0.2` | `PRIORITY-POLICY.md`; `afterword.policy.POLICY_VERSION` |
| B1 heuristic | `hb-v0.2` (length threshold 281 prose characters) | `afterword.heuristic.HEURISTIC_VERSIONS` |
| B2 prompt | `pr-v0.2` | `afterword.classifier.PROMPT_VERSION` |
| B2 model | Ollama, `llama3.1:8b-instruct-q4_K_M`, digest `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | `afterword.providers.ollama.PINNED_DIGESTS` |
| B2 options | `num_ctx=4096;num_predict=200;seed=20261003;temperature=0` | `afterword.providers.ollama.options_key` |
| Duplicate-flag rule | strict (`MALFORMED`, surfaced) | `EVALUATION.md`, decided 2026-10-18 |
| Ingestion | `dev-sync-0.1` | `afterword.adapters.dev.sync.INGESTION_VERSION` |
| Application | `0.2.0`, bumped in the preparation commit before the seal; the seal commit is tagged `prereg-v1` | `pyproject.toml`; `afterword.__version__` |
| Dependencies | `uv.lock` at that commit | `uv.lock` |
| Accrual basis and volume-split median | run `20261026T181641Z` (decided 2026-10-27: not replaced by the seal-day probe) | `EVALUATION.md` |

**Application version (decided: `0.2.0`).** `0.1.0` had not changed since the first code was written, so on its own it did not identify the code that ran. It is bumped to `0.2.0` in the preparation commit that lands before the seal (moved there by the author on 2026-10-27), and the `prereg-v1` tag names the seal commit, which changes no code.

**Ollama itself** is not pinned; the model digest and options are. A server update between weeks could in principle change outputs for the same digest and options. Recording the Ollama version with each `shadow run` is not built; noting it by hand in the weekly commit message (`ollama --version`) costs nothing.

## The accrual estimate and the volume-split median (run `20261026T181641Z`)

Recorded in `EVALUATION.md` v21 (2026-10-26 entry). In short: the consequential share is 158 of 494 (32.0%; 28.0% to 36.2%), and 69 of 167 (41.3%) on the `lg-v0.7` labels, so 20 consequential comments need about 63 comments at 32.0% (72 at the interval's low end) and about 49 at 41.3%: the 100-comment target binds. Trailing 13 complete weeks (2026-07-27 to 2026-10-25): mean 23.62, median 19 per week; 100 comments in about 5 weeks at the mean, 6 at the median; a replay of those weeks reaches both targets in 3 to 7 weeks (median 5). The volume-split median is **19** comments from others per week. Decided by the author 2026-10-27: these are the registered values, and the seal-day probe does not replace them.

## The preregistration record

Written on seal day by `afterword preregistration write` (added 2026-10-26), which sets `registered_at` to the current UTC time, to the second, takes the other fields from the application's pins (so shadow mode's checks pass), and refuses if the record already exists. It is not written earlier because every tool reads it as soon as it exists. The record it writes:

```json
{
  "registered_at": "<the time `preregistration write` runs, UTC, ending in Z>",
  "b1_heuristic": "hb-v0.2",
  "b2_provider": "ollama",
  "b2_model": "llama3.1:8b-instruct-q4_K_M",
  "b2_model_digest": "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
  "policy_version": "pp-v0.2",
  "num_ctx": 4096,
  "excluded_posts": []
}
```

## The corpus export, prepared

The full seal-day sequence, including the export, is `PREREGISTRATION.md` Step 5.

- The probe and ingest come first and as close to `registered_at` as practical: the export takes the store as it is, so a `dev` comment created before `registered_at` but not yet ingested would be missing from `v1`. Nothing is published between the probe and the pushed commit.
- `corpus export` writes `fixtures/corpus/v1/dev.jsonl` (git-ignored, with text) and `registry/corpus-v1-dev.json` (committed, IDs and hashes only), once; `corpus verify` must say verified.
- Running the export on real data is the author's (`CLAUDE.md`).
