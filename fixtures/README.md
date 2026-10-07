# Fixtures

Fixtures support repeatable ingestion and classification tests without live API calls, and hold the versioned evaluation corpus.

## Rules

- Never commit API keys, tokens, cookies, email addresses, or other secrets.
- Prefer minimally sufficient source payloads.
- Preserve source field names in adapter fixtures.
- Store normalized expected output separately from raw source fixtures.
- Mark every fixture as `synthetic`, `redacted-real`, or `public-real`.
- Real comments are handled per `docs/PRIVACY-AND-BOUNDARIES.md`, including purge on upstream deletion.
- Real comment text is not committed to a public repository. Public commits contain manifests and synthetic fixtures only; real corpus text lives in a git-ignored directory.

## Layout

Entries marked *(planned)* do not exist yet: the real corpus is not frozen until preregistration (ADR-010).

```text
fixtures/
  dev-api/
    source/            # synthetic DEV payloads (MANIFEST.md); real/ is git-ignored
    expected/          # normalized expected output for the synthetic payloads (norm-v0.1)
  corpus/
    MANIFEST.md        # public: every corpus file, how it was made, its SHA-256
    adversarial.jsonl  # synthetic, public: the adversarial set (EVALUATION.md)
    synthetic-bench.jsonl  # synthetic, public: class-balanced set for model benchmarks only
    v1/                # git-ignored: real comment text (planned)
      dev.jsonl
      test.jsonl       # prospective, accrued after preregistration (ADR-010)
  labels/              # git-ignored, written by `afterword label`
    <corpus_version>/
      initial.jsonl
      calibration.jsonl
      self_agreement.jsonl
      batches.jsonl
```

## Synthetic sets (`corpus/*.jsonl`)

Schema, provenance, and hashes are in `corpus/MANIFEST.md`. Each record carries source-shaped HTML, so it goes through the same normalization as a real comment. `.gitattributes` keeps hashed fixtures LF on every platform.

## Corpus record (`corpus/v1/*.jsonl`)

```json
{"comment_id": "1a2b", "source_object_id": "1a2b", "content_id": "p_017", "corpus_set": "test", "body_text": "...", "parent_comment_id": null, "context_as_of": "2026-03-14T09:12:00Z", "provenance": "public-real", "normalization_version": "norm-v0.1"}
```

`comment_id` is the source comment ID (DEV `id_code`), which is stable across runs. It is a string, and some values are all digits. Before the corpus is frozen, labels exist without a corpus record and join to it later on `comment_id`.

## Label record (`labels/<corpus_version>/<pass>.jsonl`)

```json
{"label_id": "l_1a2b_initial", "comment_id": "1a2b", "snapshot_run_id": "20261009T170000Z", "corpus_version": "unfrozen", "corpus_set": "dev", "sample_kind": "researcher", "label_guide_version": "lg-v0.1", "taxonomy_version": "tax-v0.1", "normalization_version": "display-v0.1", "primary_class": "CORRECTION", "flags": ["REFERENCES_SPECIFIC_CLAIM"], "consequential_prospective": 3, "consequential_retrospective": 3, "consequential_retrospective_state": "PRESENT", "context_reconstructed": true, "replied_before_labeling": false, "reason": "Step 2 command is wrong for current CLI", "pass": "initial", "batch_id": "b_20261009T184000Z", "duration_seconds": 48.2, "labeled_at": "2026-10-09T18:40:00Z"}
```

- `flags`: from `tax-v0.2`, the structural flags (`REPLY_TO_AUTHOR`, `CONTAINS_CODE`, `CONTAINS_LINK`) come first, set by the tool (code and link from `norm-v0.1` of the comment's source body), then the labeler's. Analysis uses the deterministic code and link flags for every label, whatever its `taxonomy_version` (`docs/TAXONOMY.md`).
- `snapshot_run_id`: the probe run the comment and its context were read from. Provenance, not identity.
- `normalization_version`: the text rendering the labeler saw. `display-v0.1` is the labeling tool's display rendering, not the Stage 2 classification normalization.
- `corpus_version`: `unfrozen` until `dev` is frozen at preregistration.
- `corpus_set`: `dev` (the default; every historical comment) or `test` (prospective comments, labeled with `--set test`; ADR-010).
- `sample_kind`: who produced the label and how the comment was sampled. Every V1 label is `researcher` (the author's own labeling of `dev` or `test`; `docs/EVALUATION.md`). Other sources, such as random collapsed-tier audits or targeted exercises, are a future design (`docs/LABELING-AT-SCALE.md`) and would add values, never reuse this one. Labels written before the field existed (2026-10-03, before session 5's change) have no `sample_kind`; they are researcher labels, and readers treat an absent value as `researcher`. Existing label records are never rewritten to add it.
- `consequential_retrospective_state`: `PRESENT`, or `UNKNOWN` when the labeler skipped the retrospective grade (the grade is then `null`).
- `context_reconstructed`: see `docs/LABELING-GUIDE.md`.
- `replied_before_labeling`: `true` when the author's direct reply to the comment exists in the snapshot. Derived by the tool, not chosen. A prospective grade given after replying may carry hindsight.
- `pass`: `initial`, `calibration` (a re-label from scratch of a comment with an initial label, written to `calibration.jsonl`; never overwrites), or `self_agreement`. Which label analysis uses is in `docs/LABELING-GUIDE.md`.
- `batch_id` and `duration_seconds`: the labeling batch, `b_<start time>`, with `_2`, `_3` appended when another batch already started in the same second (start and end times, and the post order with its seed when shuffled, are in `batches.jsonl`; a `batch_start` without `post_order` predates the option and was `published`; `tool` on `batch_start` is `terminal` or `browser`, absent before 2026-10-04; `post_panel` on `batch_start` is `true` when the post panel was available for the batch (the label UI, with a run that captured post bodies), absent before 2026-10-07; a terminal `batch_end` carries `abandoned_in_progress`, true when the session stopped with answers entered for the comment on screen, which were not saved) and the time from the comment being shown to the label being saved.

## Freezing

`dev` is frozen by committing its manifest hashes at preregistration. The prospective `test` set is sealed differently (ADR-010): each week's shadow-mode classifier outputs are written to a git-ignored file whose hash is committed that week, and nothing is revealed until accrual stops. A changed hash means a new corpus version.
