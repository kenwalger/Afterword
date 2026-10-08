# Future Features

**Status:** Future design note. Not in V1 scope. Every feature here is gated on the Stage 3 result: each assumes that classification on real data is trustworthy, which is exactly what V1 has not yet shown.

**Version:** 4 (2026-10-08)

v4 adds "Multilingual comments" with proposed claim C-020 (appended to `CLAIMS.md`, DEFERRED UNTIL STAGE 3 GATE), and a parking-lot note on counting human and disclosed-AI comments separately.

v3 records that the proposed claims C-013 to C-019 are in `CLAIMS.md` (status DEFERRED UNTIL STAGE 3 GATE), and adds a parking lot.

v2 adds features for high-volume and team accounts (duplicate-question clustering, an unanswered-questions queue, and feedback extraction through output adapters) and a set of discovery questions for people with larger comment volumes.

## Why these exist

V1 asks whether assisted triage reduces the author's review effort. Early evidence suggests that, for this author, the time saved is modest: a typical week takes about 4 minutes to read, a busy week about 17, and under `pp-v0.1` most comments are legitimately worth seeing (`CLAIMS.md`, C-009 and C-012; the oracle-ceiling observation in `EVALUATION.md`).

That points at value of a different shape than "fewer comments to read." This note records candidate features that reuse the V1 foundation, first for the author and then for high-volume and team accounts, each with a proposed claim and its falsifier, so they are tested rather than assumed.

## Shared foundation

All of these reuse what V1 builds: ingestion and lifecycle, normalization, the store, classification, the priority policy, provenance, and the application service layer (ADR-012). All of them also need three things V1 does not yet have:

1. **Incremental, scheduled sync** (Stage 1 completion), so refreshes are cheap.
2. **A review surface:** a digest page or the Stage 4 review UI.
3. **A passed Stage 3 gate on real data.**

## 1. Spike insurance

**What:** when a post receives unusual volume, deliver a short digest of the comments most worth seeing first.

**Why:** the cost of chronological review is concentrated in busy weeks (C-009). In a spike, the risk is not wasted time but a buried correction.

**Reuses:** the classifier and policy almost entirely. The product is the `SURFACE` tier, delivered when it matters.

**Adds:**

- Spike detection from the volume data the baseline already computes (for example, a post exceeding the trailing-13-week p90 weekly volume within 48 hours).
- Scheduled sync and a short digest: "This post is busy. These are worth seeing first."

**Hard part:** the `SURFACE` list must be short and trustworthy. A model that surfaces most comments makes the digest useless. This depends on the flag-design decision recorded in `EVALUATION.md` (evidence-required or informational-only flags).

**Claim:** C-012 already covers it: assisted triage delivers most of its value in high-volume weeks.

## 2. Propagation ledger

**What:** record, and later query, what comments led to: corrections, new articles, code changes, experiments, retained claims.

**Why:** the author's own sense of a comment's value is what it changed. No existing tool tracks this.

**Reuses:** `PropagationEvent` and `Disposition` are already in `DATA-MODEL.md`, and "which comments caused a change to one of my projects?" is the first candidate external query in ADR-012.

**Adds:**

- Fast recording in the review surface or CLI.
- Links to targets: articles, commits, issues.
- **Assisted suggestions** of candidate links for the author to confirm, never to accept silently: a commit message that mentions a comment URL, a later post on the same topic, an edit to the post shortly after a correction.
- An optional one-time backfill from memory for historical comments.

**Hard part:** human effort. C-007's falsifier is that propagation is too burdensome to record consistently.

**Proposed claim, C-013: assisted suggestions make propagation recording sustainable.**

- Evidence needed: over a defined period, the share of consequential comments with a recorded propagation outcome, with and without suggestions, and the share of suggestions the author accepts.
- Would weaken or falsify: recording rates stay low with suggestions, or most suggestions are rejected.

## 3. Rediscovery

**What:** resurface past material worth revisiting.

**Why:** labeling the historical corpus showed that old threads hold ideas the author had forgotten.

**The cheap version needs no new model work.** Classification, grades, and structural reply data already answer questions such as:

- consequential questions the author never answered
- technical extensions graded 2 or higher from more than a year ago
- opportunities with no recorded disposition

**The topical version** ("you are writing about caching; here is what was said about caching before") needs search. Keyword search is cheap (SQLite full-text search). Semantic search needs embeddings, which is a new model boundary and needs its own ADR (ADR-012). Local embeddings through Ollama would keep the property that nothing leaves the machine.

**Boundary:** rediscovery by topic is in scope for this feature. Rediscovery by commenter ("what has this person said?") is the C-005 question and requires the reputation-bias evaluation and its own ADR first.

**Proposed claim, C-014: rediscovery surfaces material the author judges worth revisiting.**

- Evidence needed: for rediscovery digests over a defined period, the share of surfaced items the author marks as worth revisiting, and how many lead to a recorded action (reply, propagation, new work).
- Would weaken or falsify: most surfaced items are judged not worth revisiting, or none leads to action.

## 4. Reply context and position history

**What:** when the author replies to a comment, show what the author has previously said on the same topic, with links, in date order, so the reply is informed by the author's own history. Optionally, show how the author's position has changed over time.

**Example:** the author publishes a post about dogs. A commenter writes about Siberian Huskies. When the author opens that comment to reply, a panel lists the author's own earlier posts, comments, and replies about Siberian Huskies, each linked and dated. A position timeline shows that the author was lukewarm on the breed in 2019 and enthusiastic by 2025, with the posts and replies where that changed.

**Why:** a reply that knows what the author said before is more consistent, avoids repeating or contradicting old statements unknowingly, and can acknowledge a change of mind openly ("I used to think otherwise; here is what changed"). It also connects to judgment drift (`LABELING-AT-SCALE.md`, C-011): the same idea, applied to the author's public positions rather than private labels.

**Privacy shape:** this feature is built on **the author's own words**: their posts, comments, and replies. It does not profile commenters. Other people's comments may appear as context only where the author's reply is attached to them, and grouping material by commenter remains out of scope without the C-005 ADR.

**Reuses:** the store, normalization, provenance, and the service layer. It is a natural external query too ("what have I said about Siberian Huskies?", ADR-012).

**Adds:**

- **Ingesting the author's post bodies,** not only titles, so posts can be searched. This is the author's own content, retrieved through the same connection.
- **Topical retrieval** over the author's posts, comments, and replies: keyword search first, semantic search (local embeddings) later under its own ADR.
- **A reply-context panel** in the review surface, showing matches newest first or oldest first, each with its date and a link.
- **An optional position timeline.**

**The position timeline must stay grounded.** The risk is a model inventing a tidy story of intellectual evolution. Rules:

1. **Excerpts first.** The baseline timeline is the author's own dated statements, quoted from their own text, with links. No model is needed for this.
2. **Summaries are optional and cited.** If a model summarizes how a position changed, every statement in the summary links to the excerpt it rests on. A statement with no supporting excerpt is not shown.
3. **Marked as interpretation.** A summary is labeled as model-generated, distinct from the author's own words.
4. **The author is the authority.** The author can dismiss, correct, or annotate the timeline ("I changed my mind because of X"), and those annotations are stored as the author's own records.

**Hard part:** retrieval quality. Topic matching that is too loose buries the panel in noise; too strict, and it misses the thread where the change of mind actually happened.

**Proposed claim, C-015: reply context improves the author's replies.**

- Evidence needed: over a defined period, how often the author opens the panel, how often a shown item is marked relevant, and how often the author reports that it changed or informed the reply.
- Would weaken or falsify: the panel is rarely opened, or shown items are mostly judged irrelevant.

**Proposed claim, C-016: position summaries are faithful to their sources.**

- Evidence needed: an audit of generated position summaries, checking every statement against its cited excerpt.
- Would weaken or falsify: summaries contain statements not supported by their citations, or the author frequently judges them to misrepresent their views.

## For high-volume and team accounts

People with much larger comment volumes than the V1 author do not just have more of the same problem. Some problems only appear at scale. These three are the most promising for large individual accounts and for DevRel, docs, or content teams. They are recorded as candidates to validate with those users (see Discovery questions below), not commitments.

### 5. Duplicate-question clustering

**What:** group comments that ask the same question in different words, so the author answers once, links that answer from the others, and fixes the post or adds an FAQ entry so the question stops arriving.

**Why:** at volume, the most expensive pattern is often not one buried correction but the same question arriving many times across a week, each needing an answer.

**Reuses:** classification (questions are already identified), the store, and the Stage 5 theme clustering on the roadmap.

**Adds:**

- Similarity across comments. Keyword overlap gets partway; "same question, different words" needs embeddings, which requires the semantic-search ADR (shared with topical rediscovery and reply context, so that ADR serves three features).
- A cluster view: the question, its variants, which ones have been answered, and a link to the canonical answer.
- Optionally, a propagation event when a cluster leads to a post edit or FAQ entry.

**Hard part:** cluster quality. Over-merging hides genuinely different questions behind one answer; under-merging leaves the author answering the same thing repeatedly.

**Proposed claim, C-017: duplicate-question clustering reduces repeated answering at high volume.**

- Evidence needed: on a high-volume account, the share of questions that fall into clusters of two or more, the author's judgment of cluster correctness on a random sample, and the reduction in separate answers written.
- Would weaken or falsify: few questions cluster, or sampled clusters are frequently judged wrong.

### 6. Unanswered-questions queue

**What:** a list of questions the author has not replied to, oldest first, with links.

**Why:** at volume, questions fall through the cracks simply because the feed moves on.

**Reuses:** almost everything. Classification identifies questions; structural reply data shows whether the author answered. This is the cheap version of rediscovery, pointed at the present instead of the past, and could be one of the first features built after the Stage 3 gate.

**Adds:** the queue view, filters (by post, age, class), and a way to mark a question as handled without replying (answered elsewhere, no longer relevant).

**Hard part:** "answered" is not always a direct reply. The author may have answered in a post edit, another thread, or a different channel. The mark-as-handled action covers this, at the cost of some manual effort.

**Proposed claim, C-018: an unanswered-questions queue reduces questions left unanswered.**

- Evidence needed: over a defined period, the share of questions from others that receive a reply or a handled mark, compared with a prior period without the queue.
- Would weaken or falsify: the unanswered share does not change, or the queue is rarely opened.

### 7. Feedback extraction through output adapters

**What:** identify product signal in comments (bug reports, feature requests, documentation confusion) and, with the author's confirmation, send it to where the team works: an issue tracker, a chat channel, or similar.

**Why:** for a company or project account, comments are product feedback. Today that signal is copied by hand, or lost.

**Reuses:** classification, provenance, the service layer (ADR-012), and the propagation ledger (feature 2): "this comment became this issue, which became this fix."

**Adds:**

- **Output adapters.** The mirror image of ADR-001's source adapters: one adapter per destination (for example Jira, GitHub Issues, Linear, Slack), each translating a canonical feedback item into that destination's format. As with source adapters, destination-specific details stay inside the adapter, and each adapter has a capability record of what its destination supports.
- **Account-specific taxonomy extensions.** The base taxonomy only approximates product signal (a bug report usually lands in `CORRECTION` or `TECHNICAL_QUESTION`, a feature request in `OPPORTUNITY` or `TECHNICAL_EXTENSION`). Teams would want explicit categories that map to their tracker. This suggests a base taxonomy plus versioned, per-account extensions, which is a design question of its own.

**Rules specific to output adapters:**

- **Every export is confirmed by a human, per item** (ADR-003). Nothing is filed, posted, or sent automatically.
- **Exporting is a new data boundary.** Sending a commenter's text into Jira or Slack moves other people's words into a third-party system. Each output adapter needs a boundary record in `PRIVACY-AND-BOUNDARIES.md` stating what is sent. The default sends a link to the comment and a summary, not the full text.
- **Credentials per connection** (ADR-013), never global, and covered by the same credential rules as the DEV key (ADR-006).
- **Provenance both ways.** The exported item links back to the comment; Afterword records the destination item as a propagation event.

**Hard part:** each destination has its own fields, workflows, and permissions, so every adapter is real integration work. Start with one destination, chosen by what discovery conversations show teams actually use.

**Proposed claim, C-019: feedback extraction captures product signal that would otherwise be lost.**

- Evidence needed: on a team account, the number of comments exported per period, the share of exports the team keeps (not closed as invalid), and the team's estimate of how many would have been captured by hand.
- Would weaken or falsify: few comments qualify, most exports are closed as invalid, or the team already captures the same signal by hand.

### Cross-platform aggregation

Large accounts and teams have comments on many platforms at once (DEV, Hashnode, Medium, YouTube, Reddit, Hacker News). This is likely their biggest need, and the adapter architecture (ADR-001) exists for it. It is deliberately last: one platform working well comes first, and Stage 6 already makes a second source an explicit decision after V1 has evidence.

## Multilingual comments

**What:** help the author read, triage, and answer comments written in languages the author does not read, without the tool ever standing in for the comment.

**Why:** the first count on `dev` (2026-10-08, `docs/benchmarks/2026-10-08-dev-set-evaluation.md`) found 2 of 458 comments from others detected as non-English, with 5 more uncertain. Small for this author, but for a larger or more international audience a comment the author cannot read is a comment the author cannot triage, and today the pre-check cannot see an instruction written in another language (`pc-v0.1` is English-only; adversarial case `adv-110`).

**Adds:**

- **Language detection as a structural field.** Detected language, with the detector and its version, set from normalization like the code and link flags: never a judgment, never a priority input. The detector is chosen again when this becomes a runtime field (the counts-only analysis uses `py3langid`; `lingua` is the stronger candidate for short texts). Short and low-confidence texts get no language rather than a guess.
- **Local translation, shown beside the original.** Translation through a local model (Ollama), displayed next to the comment, never in place of it, and marked as machine-generated. Stored as derived data with the model, digest, prompt version, and options that produced it, purged with the comment (ADR-009), and never used as the comment's text for classification or labels unless a later, separate decision says so.
- **A model-boundary record for translation** in `PRIVACY-AND-BOUNDARIES.md`, signed off by the author before any real comment is translated. Translation is a new use of comment text, even on the local path.
- **The pre-check beyond English.** Instruction patterns for the languages actually observed, each a new pre-check version, tested on synthetic cases in those languages (including `adv-110`), with the same rule as now: a match only raises attention.
- **Optional translation of the author's reply drafts.** The author writes in their own language; a local model offers a translation; the author reviews, edits, and sends it themselves (ADR-003). Nothing is posted by the tool, and the draft and its translation stay local.
- **Labels record translation.** From `lg-v0.5` a label records `read_via_translation`, so grades given through a translation can be analyzed apart.

**Hard part:** a translation can be fluent and wrong. A correction can lose the detail that makes it a correction, and a joke or a challenge can flip in tone. The design keeps the original primary and the translation visibly secondary for that reason.

**Proposed claim, C-020: local translation lets the author triage and answer non-English comments without misreading them.**

- Evidence needed: on non-English comments, the author's grade made through the translation against a later grade made with a fluent reader's help or a second translation (agreement on the consequential binary), the share of translations the author judges misleading, and whether any consequential non-English comment was missed.
- Would weaken or falsify: grades through translation disagree often with the checked grades, translations the author judges misleading are common, or non-English comments are too rare for the feature to matter.

## Discovery questions for high-volume accounts

Before building anything for larger accounts, find out whether the problem exists for them, how they handle it today, and whether a tool already does it. It is entirely possible that high-volume authors and teams already have a solution, self-built or commercial. Finding that out early is a good outcome.

### Offer first: measure the problem

The read-only probe and the volume baseline (`afterword probe`, `afterword baseline`) need no model and send nothing anywhere. Offering "measure your comment problem in five minutes" gives each person their own C-009 numbers: total volume, weekly median and p90, and how spiky it is. Their numbers are better evidence than their impressions.

### Questions

1. Roughly how many comments do you receive in a typical week, and in your busiest week of the past year?
2. Where do your comments live: one platform or several? Which ones?
3. Who handles them: you alone, or a team? If a team, how is the work divided?
4. How do you handle comments today? Notifications, a daily pass, a dashboard, a spreadsheet, something else?
5. **Do you use a tool for this, self-built or commercial?** What does it do well, and what is missing?
6. What have you missed that you wish you had not: a correction, an opportunity, a question that went unanswered too long?
7. How often do you see the same question asked repeatedly? What do you do about it?
8. Do comments ever become bug reports, feature requests, or documentation fixes? How does that happen today, and where does it end up (issue tracker, chat, nowhere)?
9. How much time does comment handling take in a typical week, and in a busy one?
10. Would you run a tool locally, with a local model, or would you only use a hosted service? Would sending comments to a third-party AI provider be acceptable to you or your organization?
11. Of these, which would you actually use: a short "worth seeing first" list during busy periods, an unanswered-questions queue, duplicate-question clustering, or feedback routed to your tracker?

### Handling the answers

- Record answers in your own notes, outside the repository, unless the person agrees to be quoted.
- In anything committed or published, summarize in aggregate ("three of five teams use a shared spreadsheet") and do not name people or organizations without permission.
- Note any existing tools mentioned, with what they do and do not cover. If an existing tool already solves a problem well, record that and drop or reshape the matching feature.

## Suggested order

For the author:

1. **Spike insurance:** closest to the V1 experiment, and C-012 measures it.
2. **Propagation ledger:** Stage 5, mostly recording and queries.
3. **Rediscovery, cheap version:** no new model work.
4. **Reply context, excerpts only:** keyword retrieval over the author's own words.
5. **Topical rediscovery and semantic reply context:** after the semantic-search ADR.
6. **Position summaries:** last, and only with the grounding rules above.

For high-volume and team accounts, after discovery conversations confirm the need:

1. **Unanswered-questions queue:** reuses nearly everything.
2. **Duplicate-question clustering:** after the semantic-search ADR.
3. **Feedback extraction:** one output adapter first, for the destination teams actually use, plus the taxonomy-extension design.
4. **Cross-platform aggregation:** after one platform works well (Stage 6).

## Rules for all of these

- Nothing here starts before the Stage 3 gate.
- Each feature's claim is appended to `CLAIMS.md` before the feature is built, in the existing format. C-013 to C-019 were appended on 2026-10-07 and C-020 on 2026-10-08, each with status DEFERRED UNTIL STAGE 3 GATE; a feature's claim moves to UNTESTED, by a dated entry, when its work starts.
- Nothing acts on the author's behalf. Every feature informs; the author decides (ADR-003). That includes every export through an output adapter.
- Local first (ADR-013). Any new model boundary, such as embeddings, is recorded in `PRIVACY-AND-BOUNDARIES.md` before use.

---

## Parking lot

Ideas noted but not designed. Nothing here is planned.

- **Community Gems.** Show which of the author's posts, and which comments on them, earned DEV gems, and compare gemmed comments with comments labeled consequential. First check whether the API exposes gems at all. (2026-10-04)
- **Reaction counts are not a reliable engagement metric.** One person can add up to five reactions to a post, so the aggregate cannot be read as unique reactors or as approval. Do not use reaction counts as a proxy for reach or approval without a per-user breakdown, which the API likely does not expose. (2026-10-05)
- **Count human and disclosed-AI comments separately.** Any dashboard or report that counts comments shows comments whose author disclosed AI use separately from the rest, from platform disclosure fields only and never inferred from style (`PRIVACY-AND-BOUNDARIES.md`, "AI authorship"). Comments disclosed as hand-written (`no_ai` on DEV) count as human; "not disclosed" is its own bucket, never folded into either. (2026-10-08)
