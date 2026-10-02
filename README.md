# Afterword

Assisted comment triage for technical publishing. A scoped experiment, not a product.

Afterword asks whether AI can reduce the part of a comment stream that needs immediate human review without hiding the comments that matter most.

**Core boundary:** the system may organize attention. It does not decide whose voice the author is permitted to hear.

## Status

Stage 0 of `docs/ROADMAP.md`, in progress. V1 is DEV-only; other platforms are deferred until the primary experiment produces evidence.

Done:

- Experiment design (docs and ADRs), committed before any code.
- A read-only DEV probe (`afterword probe`) that verified the capability matrix, including edit and deletion behavior.
- The C-009 volume baseline (`afterword baseline --run <run>`): 432 comments from others across 138 posts, recent and spiky. Review time is not yet measured.
- A local labeling tool (`afterword label`), including a chronological timing mode for C-009.

Open: the corpus targets decision (`docs/proposals/`), timed chronological reviews, labeling, and the adversarial set. No classifier exists yet.

## Development

After cloning, install the pre-commit hook. Git does not carry hook settings in a clone, so every fresh clone needs this once:

```text
git config core.hooksPath scripts/hooks
```

The `pre-commit` hook rejects staged files containing em-dashes or bidi control characters, then runs the identity scan (`scripts/check_committable.py`), ruff, ruff format, mypy, and pydoclint. The `commit-msg` hook rejects em-dashes and bidi control characters in the commit message. The full check list, including tests on both supported Pythons, is in `CLAUDE.md`:

```text
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy && uv run pydoclint src scripts
uv run pytest
uv run --isolated --python 3.12 pytest
```

Commands that call DEV read the key from `DEV_API_KEY` (for example `uv run --env-file .env afterword probe`). Real payloads, reports, and labels are written only to git-ignored paths.

## Reading order

1. `docs/PROJECT-BRIEF.md`: the question and why it matters
2. `docs/SCOPE.md`: what V1 is and is not
3. `docs/LABELING-GUIDE.md`: what "consequential" means and how ground truth is produced
4. `docs/TAXONOMY.md`: comment classes and flags
5. `docs/PRIORITY-POLICY.md`: how classes become priority, and where the review threshold sits
6. `docs/EVALUATION.md`: how the claims are tested
7. `docs/CLAIMS.md`: what is being claimed, before evidence exists
8. `docs/DATA-MODEL.md`
9. `docs/PRIVACY-AND-BOUNDARIES.md`
10. `docs/API-CAPABILITY-MATRIX.md`
11. `docs/ROADMAP.md`
12. `docs/adr/`
13. `docs/proposals/`: changes under discussion, and accepted ones with their evidence
14. `docs/FRICTION-LOG.md`

## Public deliverable

The primary public artifact is the evaluation write-up: what was claimed, how it was measured, what the classifier missed and why. A negative or reframed result is a valid outcome and will be published as one.

## Name

An afterword is what comes after the text is finished. Comments are the afterword readers write. The project is about what the author does with it.

## License

Apache License 2.0 (`Apache-2.0`). See `LICENSE` and `NOTICE`.
