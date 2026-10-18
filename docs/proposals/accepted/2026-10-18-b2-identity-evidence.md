# Evidence for the author's decision: which model is B2 (Llama, B1-only, or neither)

**Status:** evidence for a decision, 2026-10-18 (session 11, Part B3); no recommendation was made. **Decided by the author, 2026-10-18: B2 is Llama** (`llama3.1:8b-instruct-q4_K_M`, pinned digest), **with B1 as the baseline.** The decision and the trade-offs are recorded in `EVALUATION.md` ("Which model is B2", v17) and `CLAIMS.md` C-008. The text below is the evidence as submitted.

**Basis:** all 478 `dev` labels; B1 `hb-v0.2` and Llama (`llama3.1:8b-instruct-q4_K_M`, digest `46e0c10c039e...`, `pr-v0.2`, `num_ctx=4096`) on all 478 (Llama's last 20 classified by the author on 2026-10-18); Qwen on the 50-comment subset only (session 8); the synthetic benchmarks of 2026-10-03 and 2026-10-04. Development evidence: tuning and scoring on the same labels, made with hindsight.

"Neither" means: register no model as B2 now, and either try another model or prompt before preregistration, or run the experiment as "heuristics plus policy" (the reframe `ROADMAP.md` names for when B1 is close to B2).

## The five primary measures

| Condition | Recall | Reduction | SURFACE | Precision | Capture |
| --- | --- | --- | --- | --- | --- |
| B1, either policy | 125 of 129 (96.9%; 92.3 to 98.8) | 79 (16.5%; 13.5 to 20.1) | 199 (41.6%) | 77 of 199 (38.7%; 32.2 to 45.6) | 77 of 129 (59.7%; 51.1 to 67.8) |
| Llama, `pp-v0.1` | 129 of 129 (100%; 97.1 to 100) | 27 (5.6%; 3.9 to 8.1) | 216 (45.2%) | 79 of 216 (36.6%; 30.4 to 43.2) | 79 of 129 (61.2%; 52.6 to 69.2) |
| Llama, `pp-v0.2` | 129 of 129 | 39 (8.2%; 6.0 to 11.0) | 216 | 79 of 216 | 79 of 129 |
| Oracle, `pp-v0.2` | 129 of 129 | 103 (21.5%) | 84 (17.6%) | 54 of 84 (64.3%) | 54 of 129 (41.9%) |

By post order, Llama (`pp-v0.2`) against B1: publication order recall 39 of 39 against 36 of 39, reduction 17 against 25 of 150, SURFACE precision 27 of 71 against 27 of 63; shuffled recall 90 of 90 against 89 of 90, reduction 22 against 54 of 328, precision 52 of 145 against 50 of 136.

## For Llama

- **Recall:** misses none of 129. B1 misses 4; Llama put 2 of them at `SURFACE` (as challenges) and 2 at `QUEUE`. The difference is 4 comments, 3 of them in the publication-order labels. C-008's falsifier is "B1 matches B2 within one or two consequential comments"; 4 is outside that, narrowly, on the tuning set.
- **Class agreement** is somewhat higher: 144 of 478 (30.1%) against B1's 131 (27.4%), and in every slice (publication order 50 against 42 of 150; shuffled 94 against 89 of 328; labels added since 2026-10-08, 60 against 54 of 176).
- **Injection handling** on the synthetic sets: 8 of 10 injection cases at `SURFACE`, as for Qwen; the 2 failures (adv-109, adv-110) are pre-check gaps, not the model. `pp-v0.2` changes none of Llama's synthetic tiers on the adversarial set.
- **`pp-v0.2` costs it nothing** on `dev` and recovers 12 collapses.
- **It could carry a future consequence signal** (`docs/proposals/accepted/2026-10-18-consequence-to-tier.md`, candidate (c)); B1 cannot without a new rule.

## For B1 alone

- **Review reduction:** 79 of 478 against Llama's 39 (`pp-v0.2`): about twice as many comments set aside, at a cost of 4 consequential misses in 129.
- **SURFACE:** smaller (199 against 216) with slightly higher precision (38.7% against 36.6%). The difference is inside both intervals.
- **Cost and simplicity:** deterministic, instant, no model, no model boundary, no digest pinning. Llama took about 44 seconds per comment on the author's machine (about 6 hours for a full `dev` pass), and every prompt change is a full rerun.
- **Explainability:** every B1 decision is a rule. Llama's explanations went along with injected instructions in the synthetic benchmark even where the tier was right (Stage 4 marks them).

## Where both fall short

- **Neither is near the oracle's shape.** Both put more than 40% of comments at `SURFACE` against the oracle's 18%, at precision near 37% to 39% against 64%. Their capture is higher than the oracle's because their `SURFACE` is larger, not because they classify better.
- **They disagree on which comments surface.** Of the 129 consequential comments, B1 and Llama both put 48 at `SURFACE`; 31 are at `SURFACE` for Llama only (2 of them collapsed by B1) and 29 for B1 only; 19 are at `QUEUE` for both, and 2 more are at `QUEUE` for Llama and collapsed by B1. Over all 478 comments they give the same tier to 248 (51.9%).
- **Default-tier agreement with the labels** (whether the predicted class has the labeled class's default tier) is the same for both: 245 (B1) and 242 (Llama) of 478, about 51%.
- **Llama's judgment flags and confidence carry little:** `NEEDS_THREAD_CONTEXT` set on 249 (74 agree), `REFERENCES_SPECIFIC_CLAIM` on 256 (73 agree); confidence `HIGH` on all 478.

## For "neither"

- **Qwen** (`qwen3:4b-instruct-2507-q4_K_M`) is not a live alternative on current evidence: on the 50-comment subset it collapsed 0 under `pp-v0.1` and 3 under `pp-v0.2`, with 3 malformed outputs (duplicate flags), and under `pp-v0.2` its synthetic outputs collapse adv-007, adv-109, and adv-110.
- **The Anthropic path** (`claude-haiku-4-5-20251001`) has no signed-off model-boundary record and has never seen a real comment. Trying it means a sign-off first (`PRIVACY-AND-BOUNDARIES.md`, path B), and the result would be a secondary comparison unless chosen as B2 before preregistration.
- **A new prompt** (`pr-v0.3`, for example with the consequence signal, or with fewer judgment flags) is a full Llama rerun (about 6 hours) and more tuning on the same labels.
- **Heuristics plus policy:** register B1 alone; C-008 is then reported as "not tested", and the experiment measures C-002 with B1. This is the reframe outcome named in `ROADMAP.md`, chosen before measurement instead of after it.

## Trade-offs, side by side

| | Llama as B2 | B1 only | Neither, for now |
| --- | --- | --- | --- |
| Consequential misses on `dev` | 0 of 129 | 4 of 129 | depends |
| Comments collapsed on `dev` (`pp-v0.2`) | 39 of 478 | 79 of 478 | depends |
| SURFACE size, precision | 216, 36.6% | 199, 38.7% | depends |
| C-008 testable | yes | no | later, or no |
| Running cost per test week | about 44 s per comment, local | none | depends |
| New boundary or sign-off | none (path A signed off) | none | path B, if Anthropic |
| Time before preregistration | none beyond freezing versions | none | a prompt or model iteration on `dev` |

## What would change this picture

- A decision on candidate (b) or (c) in the consequence proposal, which would change the prompt and therefore Llama's numbers.
- The self-agreement check (`docs/proposals/accepted/2026-10-18-relabeling-scope.md`), which bounds how much any of these differences can mean: a 4-comment recall difference is within what label noise alone could produce if self-agreement on the consequential binary is poor.
