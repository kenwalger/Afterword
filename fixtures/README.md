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

```text
fixtures/
  dev-api/
    source/            # sanitized DEV payloads
    expected/          # normalized expected output
  corpus/
    MANIFEST.md        # public: versions, selection method, counts, hashes
    v1/                # git-ignored: real comment text
      dev.jsonl
      test-natural.jsonl
      test-enriched.jsonl
    adversarial.jsonl  # synthetic, public
  labels/
    v1/                # git-ignored
      initial.jsonl
      self-agreement.jsonl
```

## Corpus record (`corpus/v1/*.jsonl`)

```json
{"comment_id": "c_0142", "source_object_id": "1a2b", "content_id": "p_017", "corpus_set": "test-natural", "body_text": "...", "parent_comment_id": null, "context_as_of": "2026-03-14T09:12:00Z", "provenance": "public-real", "normalization_version": "norm-v0.1"}
```

## Label record (`labels/v1/*.jsonl`)

```json
{"label_id": "l_0142_a", "comment_id": "c_0142", "corpus_version": "corpus-v1", "corpus_set": "test-natural", "label_guide_version": "lg-v0.1", "taxonomy_version": "tax-v0.1", "primary_class": "CORRECTION", "flags": ["REFERENCES_SPECIFIC_CLAIM"], "consequential_prospective": 3, "consequential_retrospective": 3, "context_reconstructed": true, "reason": "Step 2 command is wrong for current CLI", "pass": "initial", "labeled_at": "2026-10-09T18:40:00Z"}
```

## Freezing

Test sets are sealed by committing their manifest hashes before any classifier runs on them (ADR-010). A changed hash means a new corpus version.
