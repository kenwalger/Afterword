# Friction log: session 12

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md).

## Session 12: preregistration tooling (2026-10-18)

Three decisions by the author on the preregistration list, then four tools built and tested on synthetic fixtures only: the self-agreement draw and report, `--set test` in both label tools, shadow mode, and the corpus export with its manifest. No tool was run on real data, no model was called, and no comment text was read. The author's runbook, `docs/PREREGISTRATION.md`, was matched to what was built.

### 2026-10-18 20:15 - Orientation: nothing changed since session 11

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Orientation, checking records directly.

**Expectation:** As session 11 left it.

**Observation:** Clean tree at `1d7a3fc`; no new probe run (newest `20261018T173927Z`); store 478 live comments from others, 3 placeholders; 478 analysis labels, all initial; 2 valid timing records. Check list: ruff, format, mypy, pydoclint clean; 683 tests on 3.14 and on 3.12 (isolated).

**Evidence:** `git status`, `afterword store-status`, `afterword.label_records`, `afterword.timing.load_valid` (counts only).

**Workaround:** None.

**Consequence:** It is still 2026-10-18, so only 107 labels are 14 days old; the self-agreement draw waits for 2026-10-22 as decided.

**Follow-up:** None.

### 2026-10-18 20:20 - Three preregistration decisions recorded

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Record the author's decisions on items 4 to 6 of the preregistration list.

**Expectation:** Documentation only.

**Observation:** adv-109 and adv-110 are registered as known limitations of `pc-v0.1`, with a multilingual pre-check as a V2 item; duplicate flags stay strict (`MALFORMED`, surfaced); no secondary comparisons in V1.

**Evidence:** `EVALUATION.md` v18; `ROADMAP.md` v12 (3a item closed).

**Workaround:** None.

**Consequence:** Shadow mode runs exactly two conditions, the registered B1 and B2.

**Follow-up:** None.

### 2026-10-18 20:30 - The test fake gave every post the same publication time

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Test shadow mode against the store built from the fake DEV API.

**Expectation:** The synthetic posts keep their own publication times (2026-08-03, 2026-08-17, 2026-09-07) in the store, as in the run's article list.

**Observation:** In the store every synthetic post was published 2026-08-03: the fake's single-article endpoint returned one fixture body for every post, overwriting only the ID and comment count, and the store takes `published_at` from the single fetch. The labeling tools read the list's times, so they were right; the store was not. No earlier test depended on the store's publication times, which is why it went unseen. Real DEV returns each post's own time from the single fetch.

**Evidence:** `tests/conftest.py` (`FakeDev._article`).

**Workaround:** The fake now returns the listed post's `published_at`, as DEV does. All 741 tests passed after the change.

**Consequence:** None for real data; the set boundary in the store is now tested against the right times.

**Follow-up:** None.

### 2026-10-18 20:35 - Tools built: what each does, and the choices inside them

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Build the self-agreement tools, `--set test`, shadow mode, and the corpus export (synthetic tests only).

**Expectation:** Four self-contained commands.

**Observation:** Choices made while building, each tested:

- **Where committed records live.** The preregistration record, the shadow ledger, the reveal record, and the corpus manifest go under a new `registry/` directory, not `fixtures/corpus/`, where a test requires every `*.jsonl` to be in the synthetic manifest.
- **The set boundary is a recorded time.** `registry/preregistration.json` holds `registered_at` and the registered conditions; with it, `dev` is comments on earlier posts that arrived by then, `test` is comments on posts published after it, and the rest belong to neither set (ADR-010). Without it everything is `dev` and `--set test` is refused. Chronological timing still covers every comment of the week.
- **Test comments never pass through the dev tools.** `classify` works on `dev` only, so its tier counts reveal nothing about test comments; `evaluate` and `dev-analysis` read `dev` labels only. Only `shadow run` classifies test comments, and only `shadow score`, after the reveal, scores them.
- **Sealed records hold no text.** Classifier identity and versions, class, flags, outcome, and the registered policy's tier and rule; no explanation or raw output. Canonical serialization (sorted records and keys, LF) makes the hash reproducible.
- **Failed outputs are held back.** A B2 `FAILED` (Ollama not running, say) is retried at the next run instead of being sealed for good, unless `--seal-failed`.
- **The registered conditions are checked before any model call:** the digest against the application's pin, the context size, the policy and heuristic versions.
- **A non-revealing progress command.** The runbook needed a stopping-rule check; `shadow reveal` would reveal once the rule is met. `shadow status` reports whether each target is met, never the number of test comments graded 2 or 3, because a running grade count could steer labeling (`LABELING-GUIDE.md`).
- **Blind labels only.** `shadow score` excludes labels made after the reveal and reports how many.
- **ADR-009 reaches corpus files.** Each ingest withdraws comments deleted upstream from every frozen corpus file (text out, ID kept, logged); `corpus verify` reports withdrawn records apart from changed ones.
- **The self-agreement draw reproduces the session 11 rule exactly** (sorted pool IDs, `random.Random(seed).sample`), so a draw by hand and by the command agree.

**Evidence:** `src/afterword/preregistration.py`, `shadow.py`, `corpus.py`, `label_records.py` (self-agreement), `service.py`, `cli.py`; tests `test_preregistration.py` (25), `test_self_agreement.py` (13), `test_shadow.py` (21), `test_corpus.py` (11).

**Workaround:** None.

**Consequence:** Items 2, 3, and 7 of the session 11 list are built; running them on real data is the author's.

**Follow-up:** The next entry.

### 2026-10-18 20:40 - ADR-010 says "after the commit"; the tools use a recorded time

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Implement `--set test` as asked: comments on posts published after a recorded preregistration time.

**Expectation:** The recorded time and ADR-010's boundary coincide.

**Observation:** ADR-010 defines the test set as comments on posts published after the preregistration commit. The record the tools read is committed in that commit, so its `registered_at` is necessarily a few minutes earlier. A post published in that gap would be a test post for the tools and not for the ADR.

**Evidence:** ADR-010, decision 2; `afterword.preregistration`.

**Workaround:** The runbook requires that nothing be published between `registered_at` and the pushed commit, which makes the two boundaries the same; `EVALUATION.md` v18 and the module docstring say so. The ADR is unchanged.

**Consequence:** No contradiction in practice, as long as the rule is kept.

**Follow-up:** For the author: amend ADR-010 to define test posts by the recorded time, or keep the rule.

### 2026-10-18 20:42 - The runbook matched to the commands

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** The author's `docs/PREREGISTRATION.md` (staged, written before the commands existed): add it, link it from the README and `WORKFLOW.md`, and make its commands match.

**Expectation:** Renames only.

**Observation:** Beyond names: `self-agreement draw` needs `--seed` (20261018, the recorded seed); test-set labeling and shadow mode need `registry/preregistration.json`, which the draft did not mention, so its contents and the gap rule were added; the corpus manifest is a command (`corpus export`, `corpus verify`); each week the file to commit is `registry/shadow-ledger.jsonl`; `shadow status` replaces the draft's stopping-rule check through `label status`, which shows no grades; `shadow reveal` writes `registry/reveal.json`; and `shadow score` exists. The session prompt in its Step 4 now asks for the accrual panel with `shadow status`'s counts. Labels stay in the default label directory for both sets.

**Evidence:** `docs/PREREGISTRATION.md` v2; `README.md` and `docs/README.md` (reading order); `WORKFLOW.md` v7 (section 4 follows the runbook's weekly order: label, then shadow mode).

**Workaround:** None.

**Consequence:** The runbook is the operating procedure from here; `COMMANDS.md` v4 is the reference.

**Follow-up:** None.

### 2026-10-18 20:45 - Session summary

**Goal:** Record three preregistration decisions; build and test the tools for the self-agreement check, the test set, shadow mode, and the frozen corpus; match the runbook to them.

**Completed:**
- Decisions in `EVALUATION.md` v18: pre-check gaps registered as limitations (V2 item), duplicate flags strict, no secondary comparisons.
- `afterword self-agreement draw` and `report`; `--set test` in `label`, `label-ui`, and `label status`; `afterword shadow run`, `status`, `verify`, `reveal`, and `score`; `afterword corpus export` and `verify`; ADR-009 withdrawal from corpus files at ingest. 70 new tests (753 in all), synthetic only.
- Docs: `docs/PREREGISTRATION.md` v2 (added, linked from the README, `docs/README.md`, and `WORKFLOW.md` v7), `COMMANDS.md` v4, `ROADMAP.md` v12 (3b rewritten with what remains), `DATA-MODEL.md` v14, `fixtures/README.md`, `CLAUDE.md` (scope line).

**Friction discovered:** the test fake's publication times; ADR-010's commit boundary against a recorded time; the runbook's stopping-rule check would have needed a grade count.

**Delight discovered:** the self-agreement rule drawn by hand in session 11 reproduces exactly as a command.

**Claims affected:** none.

**ADRs affected:** none changed. ADR-010's boundary wording is put to the author (above).

**Scope pressure:** the label UI's accrual panel (in the runbook's Step 4 prompt, not built); a read-only miss viewer (backlog); moving labels to a `v1` directory at the freeze (not done; labels stay in the default directory, which every command reads).

**Next smallest useful step:** the self-agreement check on or after 2026-10-22.

## Session 12: the author's decisions after the build (2026-10-18)

### 2026-10-18 21:05 - ADR-010 amended: the recorded time, and posts about Afterword excluded

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Apply the author's decisions: amend ADR-010 so test posts are those published after the recorded `registered_at`, sealed by the preregistration commit; keep labels in the default directory; exclude posts about Afterword from the test set.

**Expectation:** An ADR amendment and documentation, plus one new rule in set membership.

**Observation:**
- **ADR-010 amended 2026-10-18 (complete file).** The test set is defined by `registered_at` in `registry/preregistration.json`; the runbook keeps the rule to publish nothing between registering and committing. The 16-week cap now counts from `registered_at` too, as the code already did.
- **The exclusion changes the test set's definition, so it is in the same amendment.** Without it, excluding posts would have contradicted ADR-010 as written. The decision gives the reason (comments on articles about the experiment are about the tool, from readers who know they are measured), how a post is excluded (listed with its ID, a reason, and a recorded time; a later post by an amendment before any of its comments is labeled), and that exclusions are by post, decided before the reveal, never from classifier output.
- **Built:** `excluded_posts` in the record; set membership treats a comment on an excluded test-period post as neither set, in both label tools, `classify`, shadow mode, the corpus export, and every count and score. `afterword preregistration posts` lists the test-period posts with their IDs; `afterword preregistration exclude-post --post <id>` appends an amendment with its time, and refuses a post whose test comments are labeled unless `--after-labeling`, which marks it as late.
- **Labels made before an exclusion.** Labels carry no post ID, so the test-label counts behind `shadow status`, `reveal`, and `score` now keep only labels whose comment is a test comment now, from the store; a sealed comment on a post excluded later drops out of the counts and is reported (`sealed_no_longer_in_test_set`). Its sealed file stays as committed.
- **Labels stay in `fixtures/labels/unfrozen/`,** for both sets, before and after the freeze; `fixtures/README.md` says so.
- 15 new tests, and one reveal test split in two because its stand-in late label was on a dev comment, which the new membership filter correctly ignores (769 in all).

**Evidence:** `docs/adr/ADR-010-sealed-test-set.md`; `src/afterword/preregistration.py`, `service.py`, `labeling.py`, `cli.py`; `tests/test_preregistration.py`.

**Workaround:** None.

**Consequence:** `EVALUATION.md` v19, `COMMANDS.md` v5, `PREREGISTRATION.md` v3 (a weekly step, before labeling, to exclude any new Afterword post), `WORKFLOW.md`, `DATA-MODEL.md`, `fixtures/README.md`, and `ROADMAP.md` (item 2 of what remains, resolved). Part 1 (2026-10-27) precedes preregistration and is not a test post either way, so the list starts empty.

**Follow-up:** At each Afterword post during the test period (Parts 2 and 3): `preregistration exclude-post`, commit, then label.

### 2026-10-18 21:05 - Session summary, after the decisions

The summary above stands for the build. After it: ADR-010 amended (the recorded boundary and the exclusion rule); the exclusion built and tested; the labels directory settled; the `CLAUDE.md` scope line approved as changed. ADRs affected: ADR-010, amended 2026-10-18. Claims affected: none. What remains before preregistration is now items 1 and 3 to 8 of `ROADMAP.md` 3b. Next smallest useful step: the self-agreement check on or after 2026-10-22.
