<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/Afterword_logo_color_dark.png">
  <img alt="Afterword" src="img/Afterword_logo_color.png" width="360">
</picture>

---

Afterword is an experiment in comment triage for writers. It copies the comments on your DEV posts to your own machine, sorts them by how likely each one is to need your attention, and measures whether that sorting can spare you the routine comments without losing the ones that matter.

**The core boundary:** Afterword may organize your attention. It never decides whose voice you get to hear: every comment stays reachable, and nothing is hidden, deleted, or answered for you.

## What it has found so far

So far it has been tested on the project author's own DEV history: 302 past comments, each labeled by hand for whether it mattered. A simple rule-based sorter and a small AI model running locally both kept almost every comment that mattered (81 and 84 of 84), but both flagged more than 40% of all comments for immediate attention, where sorting that matched the writer's own judgment would flag about 18%, and the model's three extra catches came at the cost of setting far fewer routine comments aside. These are early numbers on old comments, with every caveat spelled out in [the evaluation](docs/benchmarks/2026-10-08-dev-set-evaluation.md); the real test runs on new comments as they arrive.

The article: _link to come._

## Try it on your own account

See what your own comment section looks like in numbers: how many comments you get from others, per post and per week, and how concentrated they are. This is read-only, uses no AI model, and takes about five minutes.

**Before you start, read [what Afterword does with your data](docs/USING-AFTERWORD-ON-YOUR-ACCOUNT.md):** what it collects, where it is stored, and how to delete all of it.

You need [git](https://git-scm.com/) and [uv](https://docs.astral.sh/uv/). uv installs a suitable Python (3.12 or later) if needed. The commands below are the same on macOS, Linux, and Windows.

1. **Get the code.**

   ```text
   git clone https://github.com/kenwalger/Afterword.git afterword
   cd afterword
   uv sync
   ```

2. **Add your DEV API key.** Create a key in your DEV settings, under Extensions. In the `afterword` folder, create a file named `.env` (no other extension; some editors add `.txt`) containing one line:

   ```text
   DEV_API_KEY=<your DEV API key>
   ```

   The file is ignored by git, and Afterword never prints or saves the key.

3. **Read your comments from DEV.**

   ```text
   uv run --env-file .env afterword probe
   ```

   This reads your published posts and the comments on them, one request per second, so it takes about four minutes per hundred posts. It only reads: it never posts, reacts, or deletes. When it finishes it prints a run ID such as `20261008T141450Z`. If it says `DEV_API_KEY is not set`, check the `.env` file; if it reports `/api/users/me returned 401`, DEV did not accept the key.

4. **Count them.**

   ```text
   uv run afterword baseline --run <run-id>
   ```

   This prints a short summary of your comment volume, each figure with one line saying what it means, and writes a fuller report to `reports/baseline-<run-id>.md`, which opens in any Markdown viewer.

Everything is saved inside your clone, in folders git ignores. To remove it, delete `fixtures/dev-api/source/real/` and `reports/`, and revoke the key on DEV.

## Status and expectations

- **An experiment, not a product.** It exists to answer one question with evidence: can assisted triage reduce how much of a comment stream needs immediate reading without missing what matters? A negative or reframed answer is a valid outcome and will be published as one.
- **DEV only.** Other platforms wait until the experiment has a result.
- **Expect change.** There is no installer and no review interface yet, and commands and documents change between commits.
- **Issues and findings are welcome,** especially from running the steps above on your own account: API surprises, counts that look wrong, or anything that assumed the author's machine. Please share counts and descriptions, never other people's comments.
- **Pull requests:** Issues and findings are welcome; for pull requests, please open an issue first so we can discuss.

## For contributors

Install the commit hooks once per clone (git does not carry this setting in a clone):

```text
git config core.hooksPath scripts/hooks
```

The `pre-commit` hook rejects staged files containing em-dashes or bidi control characters, then runs the identity scan (`scripts/check_committable.py`), ruff, ruff format, mypy, and pydoclint. The `commit-msg` hook rejects em-dashes and bidi control characters in the commit message.

Every check must pass before a commit, including the tests on both supported Pythons. Run them one line at a time (Windows PowerShell 5.1 does not support `&&`):

```text
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pydoclint src scripts
uv run pytest
uv run --isolated --python 3.12 pytest
```

Tests never call DEV or a model. The project's rules, including privacy, credentials, and the adapter boundary, are in `CLAUDE.md`. Real payloads, reports, and labels are written only to git-ignored paths.

## The full picture

The experiment was designed in documents before any code was written, and the documents remain the source of truth. A short reading order:

1. [`docs/PROJECT-BRIEF.md`](docs/PROJECT-BRIEF.md): the question and why it matters.
2. [`docs/SCOPE.md`](docs/SCOPE.md): what V1 is and is not.
3. [`docs/EVALUATION.md`](docs/EVALUATION.md): how the claims are tested.
4. [`docs/CLAIMS.md`](docs/CLAIMS.md): what is claimed, written before the evidence, with every later change dated.
5. [`docs/adr/`](docs/adr/): the architecture decisions, including the boundaries above.

Then, for the work itself:

- [`docs/ROADMAP.md`](docs/ROADMAP.md): the stages, their gates, and the current status.
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md): the labeling and classification routine, in order, and why.
- [`docs/COMMANDS.md`](docs/COMMANDS.md): every command, with what it reads and writes.
- [`docs/PRIVACY-AND-BOUNDARIES.md`](docs/PRIVACY-AND-BOUNDARIES.md): the privacy rules and the model-boundary records.
- [`docs/FRICTION-LOG.md`](docs/FRICTION-LOG.md): what surprised the project, session by session.

The full list, in reading order, is in [`docs/README.md`](docs/README.md).

## Name

An afterword is what comes after the text is finished. Comments are the afterword readers write. The project is about what the author does with it.

## How this was built

Afterword was developed with AI assistance. Much of the code and documentation was written in sessions with Claude Code, Anthropic's coding agent, working from designs, decisions, and labels that are the author's own. `CLAUDE.md`, at the repository root, is the standing brief each session reads before it does anything: which documents are the source of truth, which data it may never open, how credentials are handled, what it must never commit, and which checks must pass. The friction log records what happened in each session, the assistant's mistakes included. The labels, the decisions, and the judgment of what counts as consequential are the author's alone.

## License

Apache License 2.0 (`Apache-2.0`). See `LICENSE` and `NOTICE`.
