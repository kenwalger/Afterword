# Labeling Field Guide

**Version:** 2 (2026-10-07). Written against `tax-v0.2` and `lg-v0.4`.

v2 adds the post panel (`lg-v0.4`): when to open it, and the edit warning. Reviewed against `lg-v0.4` and `tax-v0.2`; nothing else needed to change.

A practical companion to `LABELING-GUIDE.md`. The guide defines what the labels mean and how ground truth is produced; this document is the checklist to keep beside you while labeling. Where the two disagree, `LABELING-GUIDE.md` and `TAXONOMY.md` win, and this document should be updated.

Most of what is here was learned the hard way, in the first 150 labels of the V1 corpus.

## Before a session

- **Use a fresh probe run** if the last one is more than a few days old (`docs/WORKFLOW.md`).
- **Use one seed for the whole pass.** Label with `--posts random --seed N`, and keep the same `N` until every comment is labeled. Write the seed in your session notes. If you switch ordering partway through a pass, note at which label count you switched.
- **Check the shortcuts** with `h` in the label UI, especially after any taxonomy change. Keys move when flags change, and a mis-keyed flag is a silent error.
- **Stop the server properly** when you finish (`q` in the page or Ctrl+C in the terminal). An open tab keeps accruing labeling time on the comment on screen.

## The post panel

`afterword label-ui` can show the post itself: press `p` (or "Show post"). It is the post as saved in the run, as plain text.

- **Open it when the comment points at the post** and you cannot recall the passage: a step, a figure, a claim. It is the fastest honest way to apply the `REFERENCES_SPECIFIC_CLAIM` test (could you point to the exact sentence?).
- **Heed the edit warning.** If the panel says the post was edited after the comment, the text you see may not be what the commenter read. A comment that corrects something you later fixed can look wrong or pointless against the edited post; grade it against what the commenter saw, as best you can tell.
- **It is not needed for every comment.** The thread and the title are usually enough. Opening the post for comments that do not refer to it only adds time.

## The grade comes first

The prospective grade (0 to 3) is the most important thing you enter. Recall is measured against it; the class is a means to that end.

- **Grade prospectively.** Ask: "If this comment had just arrived, would I want to see it before the others?" Set aside how the thread turned out, including your own reply. That knowledge belongs in the retrospective grade, which the tools ask for separately.
- **Grade separately from class.** Do not let the class decide the grade. A technical extension can be a 0. Occasionally a short acknowledgment matters, for example from someone you had hoped to hear from. If class and grade always move together, the analysis of where consequential comments sit loses its meaning.
- **Enter the retrospective grade honestly** when it differs. The gap between the two grades is evidence in its own right (C-010).

## Boundaries that change a tier

Spend your care where a decision changes whether a comment gets seen. Relax about boundaries that do not.

### Acknowledgment versus conversational

This boundary decides collapse.

- **Acknowledgment:** thanks, praise, or agreement with no further content, however long. "Great article, really enjoyed the part about caching" is still an acknowledgment if it says nothing beyond appreciation.
- **Conversational:** has some content of its own: an anecdote, a specific point, a reaction that adds something.

### Self-promotion

Under `tax-v0.2`, apply the test of what the comment does, not what it contains.

- **Spam:** promotion is the comment's main function, whether on-topic or not. Generic praise followed by a link to the commenter's product is spam.
- **Technical extension:** a substantive technical contribution that also links the commenter's work. The link supports a real contribution.
- **Opportunity:** proposes something to you: an integration, a feature, a collaboration.
- **Challenge or correction:** disputes or corrects something, then mentions a product. The dispute wins under precedence.

### Anything that might be a correction or challenge

These surface. A correction hidden inside praise is still a correction: the precedence rule assigns the earliest matching class.

## Flags

- **`REFERENCES_SPECIFIC_CLAIM`: the exact-referent test.** The flag applies only if you could point to the exact sentence, step, figure, or claim in the post the comment refers to. Engaging with the topic or the general argument ("great point about X", "I agree with your take") does not qualify. This was the most over-applied flag in early labeling (82 of the first 150 labels), and models over-apply it too.
- **`NEEDS_THREAD_CONTEXT`: only when meaning depends on the thread.** The comment would not make sense, or would be misread, without the parent or the conversation above it ("same here", "that worked for me", a terse "this is wrong"). Being a reply is not enough; a self-contained reply does not qualify.
- **Specific claims in your own replies.** `REFERENCES_SPECIFIC_CLAIM` is for the post only. A direct reply to your reply is already marked `REPLY_TO_AUTHOR`; an indirect reference to it is `NEEDS_THREAD_CONTEXT`; an error in your reply is `CORRECTION` by class.
- **Structural flags are set for you.** `REPLY_TO_AUTHOR`, `CONTAINS_CODE`, and `CONTAINS_LINK` are filled in automatically and shown read-only.
- **Judge by what the tool shows.** Flags describe the thread as of the comment. If you remember how the conversation went later, set it aside.

## Boundaries that matter less

Pick your best reading and move on:

- correction versus challenge (both surface)
- technical versus direct question (both are seen)
- which of several queue-raising flags applies

## Honesty and blinding

- **`UNCERTAIN` is a legitimate label.** An honest "I can't tell" is worth more than a forced guess, and clusters of them show where the taxonomy needs work.
- **Judge the comment, not the commenter.** Do not check profiles or history.
- **Use the reason box for hard cases.** A few words ("on-topic self-promotion; generic praise") make decisions consistent and visible later, and hard cases are candidates for the adversarial set and the calibration exercise.

## Fatigue

- Batches of at most 40.
- Stop when you notice yourself speeding up or skimming.
- Shorter, fresher sessions beat long ones. Label quality drifts with fatigue in ways that are hard to see afterward.

## Correcting earlier labels

Labels are never overwritten. If you believe earlier labels were wrong (most labelers' first few dozen are), use the calibration pass (`--pass calibration`): it re-offers labeled comments with the earlier label hidden, records a new label, and analysis uses the latest non-self-agreement pass. Do it once the definitions feel natural, not while you are still learning them.

## For new labelers

Before labeling real comments, work through the calibration exercise (`LABELING-AT-SCALE.md`, Labeler onboarding) when it exists. Until then, read this guide, `TAXONOMY.md`, and the grading scale in `LABELING-GUIDE.md` once before your first batch.