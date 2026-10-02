# Afterword: Project Brief

**Version:** 2 (2026-10-02)

## Working description

A personal publishing observability tool that helps an author process conversations on published work without outsourcing judgment.

The initial problem is concrete: as comment volume grows, a chronological inbox becomes a poor mechanism for deciding where limited attention should go. The system ingests comments, preserves their source context, classifies them, and surfaces the ones most likely to merit human review, while keeping every comment reachable.

## Primary question

**Can a system materially reduce the author's immediate comment-review workload while maintaining near-complete recall of comments the author judges consequential?**

The system may organize attention. It must not decide whose voice the author is permitted to hear.

## Precondition

The primary question only matters if the problem exists at the author's actual volume. Before building ingestion beyond what is needed to measure it, record the observed comment volume and distribution across the author's DEV posts (see C-009 in `CLAIMS.md`). If volume is low enough that chronological review takes minutes per week, the project continues as a methodology study and says so, rather than claiming a workload problem it cannot demonstrate.

## Initial user

The initial user is the project's author. This is deliberate: the project begins with a real corpus, known publishing behavior, and a human who can label whether comments were consequential.

The author is also a source of bias. The author has already read, and often replied to, most of the historical corpus. `LABELING-GUIDE.md` defines how that hindsight is separated from prospective judgment.

A second writer with substantially higher comment volume is the most valuable later validation case. Multi-user operation is not required for V1.

## Problem

Publishing platforms present comments as chronological activity. That works at small scale and degrades as volume grows. A short compliment, a support question, a substantive counterexample, a correction, and an opportunity can all occupy one row in the same feed while their consequences differ dramatically.

Community-management products already aggregate people and activity. This project does not reproduce them. Its narrower concern is the effect of conversation on the author's attention and thinking.

## Hypothesis

AI-assisted classification, combined with an explicit and auditable priority policy, can make a comment stream more tractable than either chronological review or simple heuristics, while preserving human authority over what matters, what deserves a response, and what changes as a result.

## V1 outcome

A user can connect DEV, ingest a bounded set of their own posts and comment threads, review normalized comments locally, see suggested classifications with explanations and a policy-computed priority, correct classifications, record dispositions, and inspect every comment regardless of priority.

## Success criteria

V1 is successful if:

1. Real DEV comments can be ingested reproducibly with source provenance intact.
2. A hand-labeled, versioned corpus exists, split into development and sealed test sets, before classifier tuning.
3. The system reduces the number of comments requiring immediate review without removing any comment from inspection.
4. Recall is high for comments the author labels consequential, reported as counts with every miss explained.
5. LLM-assisted triage is compared against a heuristic baseline, and its marginal value is stated honestly.
6. Classification errors are visible and correctable.
7. The system records what happened after review, including replies and propagation into other artifacts.
8. The DEV adapter keeps DEV-specific payload logic out of the core model.

## Failure and falsification conditions

The central hypothesis should be reconsidered if any of the following occurs:

- Consequential comments are regularly assigned below the review threshold.
- A heuristic baseline achieves comparable recall and reduction, making the model unnecessary.
- Reviewing explanations does not make errors meaningfully easier to detect.
- The author cannot label consistently with themself (see `LABELING-GUIDE.md`).
- The taxonomy proves too unstable to support useful triage.
- Processing overhead exceeds the attention saved at the author's realistic volume.
- Normalization destroys distinctions needed to understand a comment's meaning or provenance.
- The application becomes useful only after recreating a general community-management platform.

## Design principle

**Important idea missed: zero** is the aspirational direction, not Inbox Zero.

A false positive costs attention. A false negative can cost an idea, a correction, a relationship, or a change in understanding. Those costs are not symmetric, and the priority policy is designed around that asymmetry.

## Deliverables

1. The repository, including the frozen corpus manifest (not the comment text of other people; see `PRIVACY-AND-BOUNDARIES.md`).
2. An evaluation report covering baselines, consequential recall, review reduction, and a qualitative review of every consequential miss.
3. A public write-up of the experiment and its result, whatever the result is.

## Portfolio value

The project exercises API integration, provenance-aware normalization, AI classification behind an explicit policy, evaluation against human labels with honest small-sample reporting, adversarial input handling, human-in-the-loop authority, and privacy boundaries, all on a real dataset. The evaluation discipline is the point; the interface is secondary.
