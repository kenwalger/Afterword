# Friction and Delight Log

Start logging before the first API call. Record what happened at the time rather than reconstructing it later.

This file is the index of the public friction log. The entries are in one file per session under [`friction-log/`](friction-log/), moved there verbatim on 2026-10-04 (session 6), when this file had grown to about 104 KB. Each session's entries are curated from the author's git-ignored session notes and contain no real comment text, names, or handles.

## Sessions

| Session | Date | File | Entries to read first |
| --- | --- | --- | --- |
| Before code, and 1: Stage 0 implementation | 2026-10-02 | [`session-1.md`](friction-log/session-1.md) | "Deleting a comment with replies leaves an authorless placeholder" (the deletion placeholder finding behind the ADR-009 amendment); "`.env` was staged before the first commit"; "The account endpoint returns the email address"; "Comments from others are concentrated in a few posts". |
| 2: housekeeping, corpus proposal, code standards, labeling tool | 2026-10-02 | [`session-2.md`](friction-log/session-2.md) | "Corpus decision applied: prospective test set"; "Stopping rule restored to two targets; success criterion revised"; "Cause of the bidi characters found" (escapes written by the assistant arrive as the characters). |
| 3: probe progress, timing validity, workflow, service layer | 2026-10-03 | [`session-3.md`](friction-log/session-3.md) | "A practice timing run was nearly recorded as evidence"; "A replacement typical week, chosen by rule"; "`--set test` cannot select test comments yet". |
| 4: Stage 1 to 3a groundwork, part 1 | 2026-10-03 | [`session-4.md`](friction-log/session-4.md) | "The first pre-check patterns matched ordinary prose"; "The cache key covers the whole model input"; "Line-ending conversion would change fixture hashes"; "A non-ASCII scan of the session notes printed real comment text". |
| 5: label UI, store, classifier, providers | 2026-10-03 to 2026-10-04 | [`session-5.md`](friction-log/session-5.md) | "The deterministic pre-check carried the injection results (ADR-007, ADR-008)"; "Explanations complied with injections even when tiers held"; "Qwen over-flags: model-set flags raised 10 of 54 tiers"; "Label integrity check: 27 labels, not 29". |
| 6: documentation housekeeping | 2026-10-04 | [`session-6.md`](friction-log/session-6.md) | "When the terminal labeling tool writes a label" (`q` at the `Save?` prompt discards that comment); "Line endings: 45 working files were CRLF, not 11". |
| 7: labeling-facing work, then experimental changes | 2026-10-04 | [`session-7.md`](friction-log/session-7.md) | "Open items in session summaries were out of date"; "C-009: the typical week meets the falsification condition"; "The terminal tool's quit path, fixed"; "Oracle ceiling: pp-v0.1 caps review reduction near 18% on these labels"; "Removing code and link flags moved the pressure onto the others". |
| 8: housekeeping, label summary, post panel, first real data, first model runs, dev-set evaluation | 2026-10-07 to 2026-10-08 | [`session-8.md`](friction-log/session-8.md) | "The newest run is PARTIAL: the known deletion placeholder gained two keys"; "Shuffled labels disagree with hindsight more often"; "DEV's comment schema changed without notice"; "B1 collapses as much as the oracle, but surfaces far more"; "Llama's SURFACE inflation is class assignment, mostly "challenge""; "No condition is near the oracle on all five measures"; "What DEV says the AI-disclosure fields mean"; "AI-authorship proposal accepted, amended: a label field, not a flag". |

## Adding a session

At the end of each session, write the curated entries and the session summary to `friction-log/session-N.md`, then add one row to the table above: the session, its date, the file, and a pointer to the entries that matter most. Entries are never reworded or removed once recorded; a correction is a new, dated entry.

## Classification

Use one of:

- `PRODUCT` - platform/API behavior
- `DOMAIN` - comment/community semantics
- `PROJECT` - our own design/implementation
- `ENVIRONMENT` - tooling/runtime/setup
- `UNKNOWN` - cause not established

## Entry template

### YYYY-MM-DD HH:MM - Short title

**Platform:** DEV / CoderLegion / Project

**Type:** FRICTION / DELIGHT / SURPRISE

**Class:** PRODUCT / DOMAIN / PROJECT / ENVIRONMENT / UNKNOWN

**Task:** What was I trying to do?

**Expectation:** What did I expect to happen?

**Observation:** What actually happened? Preserve facts before interpretation.

**Evidence:** Endpoint, response shape, screenshot, fixture, error, or other supporting artifact.

**Workaround:** What did I do, if anything?

**Consequence:** Time cost, architectural change, missing capability, new idea, or no consequence.

**Follow-up:** Question or action, if any.

---

## Session summary template

### YYYY-MM-DD - Session summary

**Goal:**

**Completed:**

**Friction discovered:**

**Delight discovered:**

**Claims affected:**

**ADRs affected:**

**Scope pressure:** Anything that tried to sneak into V1?

**Next smallest useful step:**
