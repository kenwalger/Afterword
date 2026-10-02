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

Planned layout. Entries marked *(planned)* do not exist yet: the corpus is not selected or frozen (see `docs/proposals/`), and normalized output arrives in Stage 2.

```text
fixtures/
  dev-api/
    source/            # synthetic DEV payloads (MANIFEST.md); real/ is git-ignored
    expected/          # normalized expected output (planned, Stage 2)
  corpus/
    MANIFEST.md        # public: versions, selection method, counts, hashes (planned)
    v1/                # git-ignored: real comment text (planned)
      dev.jsonl
      test.jsonl       # prospective, accrued after preregistration (ADR-010)
    adversarial.jsonl  # synthetic, public (planned)
  labels/              # git-ignored, written by `afterword label`
    <corpus_version>/
      initial.jsonl
      self_agreement.jsonl
      batches.jsonl
```

## Corpus record (`corpus/v1/*.jsonl`)

```json
{"comment_id": "1a2b", "source_object_id": "1a2b", "content_id": "p_017", "corpus_set": "test", "body_text": "...", "parent_comment_id": null, "context_as_of": "2026-03-14T09:12:00Z", "provenance": "public-real", "normalization_version": "norm-v0.1"}
```

`comment_id` is the source comment ID (DEV `id_code`), which is stable across runs. It is a string, and some values are all digits. Before the corpus is frozen, labels exist without a corpus record and join to it later on `comment_id`.

## Label record (`labels/<corpus_version>/<pass>.jsonl`)

```json
{"label_id": "l_1a2b_initial", "comment_id": "1a2b", "snapshot_run_id": "20261009T170000Z", "corpus_version": "unfrozen", "corpus_set": "dev", "label_guide_version": "lg-v0.1", "taxonomy_version": "tax-v0.1", "normalization_version": "display-v0.1", "primary_class": "CORRECTION", "flags": ["REFERENCES_SPECIFIC_CLAIM"], "consequential_prospective": 3, "consequential_retrospective": 3, "consequential_retrospective_state": "PRESENT", "context_reconstructed": true, "replied_before_labeling": false, "reason": "Step 2 command is wrong for current CLI", "pass": "initial", "batch_id": "b_20261009T184000Z", "duration_seconds": 48.2, "labeled_at": "2026-10-09T18:40:00Z"}
```

- `snapshot_run_id`: the probe run the comment and its context were read from. Provenance, not identity.
- `normalization_version`: the text rendering the labeler saw. `display-v0.1` is the labeling tool's display rendering, not the Stage 2 classification normalization.
- `corpus_version`: `unfrozen` until `dev` is frozen at preregistration.
- `corpus_set`: `dev` (the default; every historical comment) or `test` (prospective comments, labeled with `--set test`; ADR-010).
- `consequential_retrospective_state`: `PRESENT`, or `UNKNOWN` when the labeler skipped the retrospective grade (the grade is then `null`).
- `context_reconstructed`: see `docs/LABELING-GUIDE.md`.
- `replied_before_labeling`: `true` when the author's direct reply to the comment exists in the snapshot. Derived by the tool, not chosen. A prospective grade given after replying may carry hindsight.
- `batch_id` and `duration_seconds`: the labeling batch (start and end times are in `batches.jsonl`) and the time from the comment being shown to the label being saved.

## Freezing

`dev` is frozen by committing its manifest hashes at preregistration. The prospective `test` set is sealed differently (ADR-010): each week's shadow-mode classifier outputs are written to a git-ignored file whose hash is committed that week, and nothing is revealed until accrual stops. A changed hash means a new corpus version.
