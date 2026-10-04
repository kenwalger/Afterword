# Friction log: session 4

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md). Moved here verbatim from `docs/FRICTION-LOG.md` on 2026-10-04 (session 6).

## Session 4: Stage 1 to 3a groundwork (2026-10-03)

### 2026-10-03 07:20 - The last commit holds only ADR-012

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Orientation: compare git state with the session 3 summary.

**Expectation:** Commit `cb2eac5` ("Stage 0: probe progress, timing validity, workflow, service layer") contains the session 3 work.

**Observation:** `git show --stat HEAD` lists one file, `docs/adr/ADR-012-application-service-layer-single-entry-point.md`. Everything else its message describes (`service.py`, `progress.py`, `timing.py`, `WORKFLOW.md`, the CLI, baseline, and labeling changes, their tests, and the doc edits) is still uncommitted in the working tree. Separately, `../docs/adr/ADR-013-local-first-hosted-path-preserved.md` is staged as an empty file, its content is unstaged, and its name uses four digits, as ADR-012's did before the author renamed it.

**Evidence:** `git status --short`, `git show --stat HEAD`, `git show :<ADR-0013 path> | wc -c` (0).

**Workaround:** None. Nothing committed or staged by this session.

**Consequence:** Session 4 work would land in the same working tree as uncommitted session 3 work unless the author commits session 3 first.

**Follow-up:** Author: commit the session 3 work (the existing message fits it), and decide on the ADR-013 file name.

### 2026-10-03 07:45 - Policy gaps closed as clarifications, not a new version

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Implement `pp-v0.1` as pure, tested code.

**Expectation:** `PRIORITY-POLICY.md` specifies everything the code needs.

**Observation:** Four things were unspecified: the form of model confidence, the confidence floor ("set during Stage 3a", no value), what "edited since it was last reviewed" means before review records exist, and which rule `rule_applied` names when several apply.

**Evidence:** `docs/PRIORITY-POLICY.md` before this session.

**Workaround:** Recorded as a dated clarification of `pp-v0.1`, since no classification existed and no tier, default, or override changed: confidence is `LOW`/`MEDIUM`/`HIGH` (author's decision); the floor is off in `pp-v0.1` and setting it is `pp-v0.2`; "edited since review" means lifecycle `EDITED` until Stage 4; rules have names, all firing rules are recorded in `rules_fired`, and `rule_applied` is the first in table order that reaches the final tier (the class default only when no override reaches it).

**Consequence:** `DATA-MODEL.md` v5 adds `rules_fired`. `src/afterword/policy.py` tests every class, every override, and, exhaustively, that no combination of flags, confidence, floor, and edit state lowers a tier.

**Follow-up:** Choose the floor on `dev` in Stage 3a (`pp-v0.2`).

### 2026-10-03 07:50 - The cache key covers the whole model input

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Define the classification cache key (incremental classification).

**Expectation:** Key on the comment's normalized-text hash plus provider, model, prompt, and taxonomy versions.

**Observation:** The classifier also receives the post title and, for a reply, the parent's text. Keyed on the comment's text alone, an edited parent would never trigger reclassification.

**Evidence:** `docs/PRIVACY-AND-BOUNDARIES.md`, default context.

**Workaround:** At the author's decision, the key is the SHA-256 of the canonical serialization of everything sent (`input_hash`), plus provider, model ID, model digest, prompt version, and taxonomy version. `MALFORMED` results are cached (deterministic at temperature 0); `FAILED` results are retried.

**Consequence:** `DATA-MODEL.md` v5.

**Follow-up:** Implement in step 8.

### 2026-10-03 07:55 - Local models pulled and pinned by digest

**Platform:** Project

**Type:** DELIGHT

**Class:** ENVIRONMENT

**Task:** Pull the two approved Ollama models after checking the tags exist.

**Expectation:** Tags may have moved or been renamed.

**Observation:** Both tags exist in the Ollama library, and the local digests after pulling match the short digests shown there:

- `qwen3:4b-instruct-2507-q4_K_M`: `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` (2,497,293,803 bytes, Apache-2.0)
- `llama3.1:8b-instruct-q4_K_M`: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` (4,920,753,328 bytes, Llama 3.1 Community License)

Ollama 0.34.3, CPU only (13th Gen Intel Core i7-1355U, 10 cores, 12 threads, 32 GB RAM).

**Evidence:** ollama.com library tag pages; `ollama list`; `GET /api/tags`.

**Workaround:** None needed.

**Consequence:** These digests are what the Ollama provider will verify before every run. A changed digest under the same tag will be refused.

**Follow-up:** Benchmark on synthetic fixtures after the checkpoint.

### 2026-10-03 08:00 - Anthropic's retention and training terms, checked before drafting

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Draft the model-boundary record for the Anthropic path.

**Expectation:** Write retention from memory.

**Observation:** The published terms were checked instead. Anthropic's privacy center says API inputs and outputs are deleted within 30 days unless another agreement applies, the input is flagged for a Usage Policy violation (up to 2 years), or the law requires it (article dated 2026-07-01). Commercial API data is not used for training by default (article dated 2026-08-18).

**Evidence:** `docs/PRIVACY-AND-BOUNDARIES.md` v3, Path B, with sources.

**Workaround:** None needed.

**Consequence:** The record states that this path sends other people's comment text to a third party that keeps it for up to 30 days. It is a secondary comparison only, with no sign-off yet.

**Follow-up:** The author signs off each path before any real comment goes through it.

### 2026-10-03 08:10 - The first pre-check patterns matched ordinary prose

**Platform:** Project

**Type:** FRICTION

**Class:** DOMAIN

**Task:** Write the deterministic `POSSIBLE_INSTRUCTION_TEXT` pre-check (`pc-v0.1`).

**Expectation:** A list of injection phrases is enough.

**Observation:** Broad first patterns would have surfaced ordinary technical comments: "for the model" (common in AI posts), "attention model", "compiler flags:", "give priority to", "the output should be", "never prioritize". The author writes about AI, so model vocabulary in comments is normal. The patterns were narrowed to forms addressed to an automated system or to this comment's classification. Two injection forms remain known gaps and are in the adversarial set: an instruction with no trigger phrase, and a non-English one.

**Evidence:** `tests/test_precheck.py` (24 flagged forms, 11 ordinary sentences not flagged); `fixtures/corpus/adversarial.jsonl` cases `adv-109` and `adv-110`.

**Workaround:** None needed.

**Consequence:** ADR-008 accepts false positives. They are kept rare so the pre-check is not a reason to ignore `SURFACE`. Writing a taxonomy class name in capitals ("CORRECTION:") is flagged, an accepted false positive.

**Follow-up:** Count pre-check hits on `dev` once the store exists (a count only, no text) to measure the false-positive rate.

### 2026-10-03 08:15 - The draft heuristic collapses short corrections

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Run B1 (`hb-v0.1`) through the policy on the synthetic sets.

**Expectation:** The heuristic would catch at least the explicit corrections.

**Observation:** With a 280-character length threshold, B1 collapses most short synthetic comments, including all three short corrections and both short-correction adversarial cases ("Off by one: limit 10 lets 11 through" has no question mark and no lexicon word). Long praise is queued by length, and "breaks" in a casual remark is a correction. Every injection the pre-check catches surfaces whatever B1 says.

**Evidence:** B1 over `fixtures/corpus/*.jsonl`; `tests/test_synthetic_sets.py`.

**Workaround:** None. The synthetic sets are not for tuning.

**Consequence:** None yet. EVALUATION.md says B1 is finalized on `dev`, and the synthetic results say nothing about real comments. It does show that a length threshold and a six-word lexicon miss the "very short but important correction" case by construction.

**Follow-up:** Tune the threshold and lexicon on `dev`; each change is a new heuristic version.

### 2026-10-03 08:20 - DEV's code-block chrome would leak into normalized text

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Normalize code blocks for classification.

**Expectation:** A code block is a `pre` element.

**Observation:** DEV's rendered HTML (from DEV's public markup, not from any real payload) wraps a highlighted `pre` in a panel with icon buttons whose SVG titles read "Enter fullscreen mode" and "Exit fullscreen mode". A tag-stripping normalizer would add those words to every comment with code.

**Evidence:** `tests/test_normalize.py` (`DEV_CODE_BLOCK`, synthetic).

**Workaround:** `norm-v0.1` drops `svg`, `button`, `script`, `style`, `template`, and `noscript` content, takes the language from the `pre` class, and keeps code whitespace.

**Consequence:** The exact wrapper markup in real comments is not verified, since real payloads are not opened.

**Follow-up:** At ingest, record a value-free count of normalized texts that still contain renderer phrases ("fullscreen mode"), so the gap would show without anyone reading a comment.

### 2026-10-03 08:25 - The tool layer turned `\u` escapes into the characters

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Write tests that use a right-to-left override, an em-dash, and combining characters.

**Expectation:** `"\u202e"` in a Python source file stays an escape.

**Observation:** The literal characters were written instead, including an em-dash and bidi controls, which the pre-commit hook rejects, and a right single quote in a regex. The cause is the tool layer, not one tool: an escape in a shell command was converted too, so a Python replacement whose target and replacement both came from escapes reported success and changed nothing.

**Evidence:** A non-ASCII scan of every touched file found four lines (counts only).

**Workaround:** These strings are now built from code points (`chr(0x202E)`, `chr(92)` for a backslash) or HTML entities (`&#8217;`). Every touched file is free of non-ASCII characters.

**Consequence:** None committed. Session 3 found the same kind of problem with a shell heredoc.

**Follow-up:** Scan touched files for non-ASCII before every checkpoint.

### 2026-10-03 08:30 - Line-ending conversion would change fixture hashes

**Platform:** Project

**Type:** SURPRISE

**Class:** ENVIRONMENT

**Task:** Record SHA-256 hashes for the synthetic sets in `fixtures/corpus/MANIFEST.md`.

**Expectation:** The committed bytes are the bytes everyone gets.

**Observation:** `core.autocrlf=true` checks out text files with CRLF on Windows, so a hash recorded from an LF file would not match a fresh checkout.

**Evidence:** `git config core.autocrlf`; earlier warnings like "LF will be replaced by CRLF".

**Workaround:** A new `.gitattributes` pins `fixtures/corpus/*.jsonl` and `fixtures/dev-api/expected/*.json` to LF. `tests/test_synthetic_sets.py` fails if a hash in the manifest is stale.

**Consequence:** Hashes hold on any checkout. The same rule will matter for the frozen `dev` manifest and the weekly sealed outputs (ADR-010).

**Follow-up:** Hash sealed outputs as bytes written by the application, never after a checkout.

### 2026-10-03 08:35 - One taxonomy module for the labeler, the heuristic, and the prompt

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Add a one-key help screen to the label prompts (the author's request).

**Expectation:** The labeling tool would show definitions already.

**Observation:** It listed class and flag names only, and kept its own copy of the lists. The help screen needed definitions, and the heuristic, policy, and prompt need the same names.

**Evidence:** `src/afterword/labeling.py` before this session.

**Workaround:** New `afterword.taxonomy` holds the classes, flags, and one-line definitions. `tests/test_taxonomy.py` checks it against `TAXONOMY.md` (precedence, flag table order, version). `h` at the class or flag prompt prints every class and flag with its definition. Labels are unchanged.

**Consequence:** A taxonomy change now fails a test until the module matches the document.

**Follow-up:** None.

### 2026-10-03 08:40 - A non-ASCII scan of the session notes printed real comment text

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Check both friction logs for forbidden characters before the checkpoint.

**Expectation:** The session notes hold only the session prompt and Claude's entries.

**Observation:** During the session, the author had added terminal output to `friction-delight-logs/session4.md`, including a chronological timing run that shows comment text. A scan for non-ASCII characters that printed matching lines brought a few of those lines, truncated, into the session. Nothing was copied anywhere. The public log was checked by phrase count (0 matches) and contains none of it.

**Evidence:** Counts only: 0 matches of the printed phrases in `docs/FRICTION-LOG.md`; the public session 4 section has 0 non-ASCII characters.

**Workaround:** Scans of the session notes now print counts or line numbers only, never matched lines.

**Consequence:** The session notes are git-ignored, so nothing is committed. Comment text from the notes reached the model session as tool output. It is not used for anything.

**Follow-up:** For the author: real comment text in the private notes is allowed, but any scan that prints matching lines will surface it. Consider keeping timing output in a separate file.

---

### 2026-10-03 - Session summary, checkpoint 1 (session 4, steps 1 to 6)

**Goal:** Stage 1 to 3a groundwork that needs no labels and no real comment data, in dependency order. The author approved the plan with a checkpoint after steps 1 to 6.

**Completed:**
- **Orientation.** The full check list passed at the start (119 tests on 3.14 and 3.12). Two inconsistencies were reported: the session 3 commit held only the ADR-012 file, and ADR-013 was staged empty under a four-digit name. The author committed session 3 and renamed ADR-013.
- **Author's decisions:**
  - The cache key covers the full model input.
  - Confidence is `LOW`, `MEDIUM`, or `HIGH`.
  - Models approved: `qwen3:4b-instruct-2507-q4_K_M` and `llama3.1:8b-instruct-q4_K_M`.
  - The Anthropic provider is built and tested under respx only, with no live benchmark this session.
- **Step 1, docs:**
  - `DATA-MODEL.md` v5: `PlatformConnection`, `connection_id` on SyncRun and ContentItem, `body_text_hash`, edit detection by normalized text, the Classification fields for kind, digest, pre-check, normalization, input hash, and raw output, the cache rule, and `rules_fired`.
  - `PRIORITY-POLICY.md`: the `pp-v0.1` clarifications.
  - `EVALUATION.md` v4: exactly one model is fixed as B2 at preregistration and the others are secondary; B1 and B2 share the pre-check and structural flags; the versioning list is extended.
  - `PRIVACY-AND-BOUNDARIES.md` v3: model-boundary records for the Ollama and Anthropic paths, neither signed off.
  - `CLAUDE.md`: current stage, `ANTHROPIC_API_KEY` rules, and storage and identity rules (ADR-013).
  - `ROADMAP.md`: the ADR range and the adversarial set.
  - README status, `fixtures/README.md` layout, and the help key in `LABELING-GUIDE.md`.
  - `tests/conftest.py` also removes `ANTHROPIC_API_KEY`.
- **Step 2, `afterword.normalize` (`norm-v0.1`):**
  - Fenced code with its language, inline code, `[text](url)` links, images, embeds, quotes, lists, and tables.
  - Renderer chrome is dropped. Control and format characters are removed. Text is NFC-normalized.
  - Structure counts and links are returned alongside the text.
  - `text_changed` compares normalized text, so a rendering change is not an edit.
  - Expected output is recorded for the synthetic DEV comments.
- **Step 3, `afterword.precheck` (`pc-v0.1`):** ten named rule groups on the normalized text, with a known-gap list.
- **Step 4, `afterword.policy` (`pp-v0.1`):** a pure `assign` that returns the tier, `rule_applied`, and `rules_fired`, with an exhaustive test that no override ever lowers a tier.
- **Step 5, `afterword.heuristic` (`hb-v0.1`):**
  - Only the EVALUATION features, computed on prose with code removed.
  - The explanation names the rule that fired.
  - It is a draft until tuned on `dev`.
- **Step 6, synthetic sets:**
  - `fixtures/corpus/adversarial.jsonl` (24 cases: every EVALUATION category, 10 injections including 2 known gaps, and 1 benign false positive).
  - `fixtures/corpus/synthetic-bench.jsonl` (30 cases, 3 per class, for benchmarks only).
  - `fixtures/corpus/MANIFEST.md` with hashes, and `.gitattributes` pinning LF.
- **Also:** `afterword.taxonomy` as the single source for names and one-line definitions. `h` at the label prompts shows them.
- **Models:** both pulled, and their digests recorded in the 07:55 entry. None has been run.
- **Checks:**
  - ruff, ruff format, mypy, and pydoclint are clean.
  - 408 tests pass on 3.14 and on 3.12 (isolated).
  - The identity scan reports 0 disallowed matches.
  - No em-dash, bidi, or other non-ASCII character in any touched file.

**Friction discovered:**
- Session 3's commit was incomplete (resolved by the author).
- The recursive listing reached `real/` (names only).
- Four policy gaps.
- The cache key had to cover context.
- Pre-check false positives on AI vocabulary.
- The draft B1 collapses short corrections.
- DEV code-block chrome would leak into normalized text.
- The editing tool turns `\u` escapes into characters.
- autocrlf would break fixture hashes.
- A line-printing scan of the session notes surfaced real comment text that the author had pasted there (nothing copied).

**Delight discovered:** Model digests matched the library on the first pull. The taxonomy module now fails a test if it drifts from `TAXONOMY.md`.

**Claims affected:** None. No model has classified anything.

**ADRs affected:**
- ADR-013 is now referenced in CLAUDE.md and ROADMAP, and the data model follows rule 3 (`PlatformConnection`).
- ADR-008 is implemented as `pc-v0.1`.
- ADR-007 is implemented as `pp-v0.1`.
- No ADR changed.

**Scope pressure:**
- **Help screen in the labeling tool:** added at the author's request. Display only; labels are unchanged.
- **`synthetic-bench.jsonl`:** added so the benchmark has class-balanced synthetic input. Marked benchmark-only, never for tuning.
- **`.gitattributes`:** added because the manifest hashes required it.
- **Service functions for the new pure modules:** not added yet. They arrive with their first caller (step 10), as ADR-012's incremental adoption allows.

**Open for the author:**
- Review the `intended` labels in the synthetic sets. They are what Claude wrote each case to be, not ground truth.
- Sign off each model-boundary path before any real comment goes through it.
- Commit this checkpoint (`commit-message.txt`).

**Next:** steps 7 to 11, after the commit: store and ingest, the classifier wrapper, the providers, service functions and CLI, then the synthetic benchmark.

