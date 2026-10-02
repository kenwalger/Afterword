# Data Model

**Version:** 4 (2026-10-02)

## Principle

A source event, a normalized representation, an interpretation, and a human judgment are different records.

Normalization must not silently convert platform-specific semantics into universal truth.

## Value states

Where a field can be absent, it carries a value state rather than a bare null:

| State | Meaning |
| --- | --- |
| `PRESENT` | Value observed. |
| `SOURCE_EMPTY` | Source explicitly returned no value. |
| `NOT_EXPOSED` | Source does not provide this field. |
| `NOT_REQUESTED` | Field exists but was not requested. |
| `INGESTION_FAILED` | Request or parse failed. |
| `NOT_YET_INTERPRETED` | Interpretation has not run. |
| `UNKNOWN` | Cause not established. |

Implementations may store this as a value plus a state column. The distinction must survive into queries where it matters.

## Source and sync

### SyncRun

One execution of the source adapter.

- `sync_run_id`
- `platform`
- `started_at`, `finished_at`
- `scope` (which posts were requested)
- `adapter_version`
- `outcome` (`COMPLETE`, `PARTIAL`, `FAILED`)
- `limitations_observed` (rate limits, truncation, errors, count mismatches, unexpected node shapes)

### SourceRecord

Append-only representation of what a source returned.

- `source_record_id`
- `sync_run_id`
- `platform`
- `source_type`
- `source_object_id`
- `observed_at`
- `source_created_at`
- `source_updated_at` (with value state; DEV comments have no edit timestamp, so `NOT_EXPOSED`, verified 2026-10-02)
- `raw_payload` (secrets and unneeded personal fields removed)
- `payload_hash`
- `ingestion_version`

A new SourceRecord is written when the payload hash for an object changes. Unchanged payloads update only `last_observed_at` on the normalized record.

A deletion placeholder's payload is a new SourceRecord because its hash differs. It contains no commenter content and is exempt from the purge; earlier SourceRecords for the same comment are purged (ADR-009).

## Normalized records

### ContentItem

- `content_id`
- `platform`
- `source_object_id`
- `author_platform_identity_id`
- `title`
- `canonical_url` (value state)
- `published_at`
- `source_record_id`

### Comment

- `comment_id`
- `platform`
- `source_object_id` (DEV `id_code`; always a string, some are all digits)
- `content_id`
- `parent_comment_id` (value state; null with `SOURCE_EMPTY` for top-level; DEV supplies it only through nesting)
- `thread_root_comment_id`
- `author_platform_identity_id` (value state; carried from the last pre-deletion observation for deleted comments; `UNKNOWN` for a comment first observed as a placeholder)
- `is_content_author` (value state; true when written by the post's author, ADR-011; carried from the last pre-deletion observation; `UNKNOWN` for a comment first observed as a placeholder)
- `body_source` (as supplied; HTML for DEV)
- `body_source_format` (`HTML`, `MARKDOWN`, `TEXT`)
- `body_text` (normalized for classification)
- `normalization_version`
- `created_at`
- `updated_at` (value state)
- `first_observed_at`
- `last_observed_at`
- `lifecycle_state` (`ACTIVE`, `EDITED`, `MISSING_FROM_SOURCE`, `DELETED_UPSTREAM`, `PURGED`)
- `deletion_evidence` (value state: `ABSENT_TWICE`, `SOURCE_PLACEHOLDER`, or `NOT_YET_INTERPRETED` while not deleted)
- `current_source_record_id`

#### Lifecycle rules

- **Edited:** payload hash changes for a known comment. State becomes `EDITED`, a new SourceRecord is stored, classification is rerun, and the priority policy raises the comment to at least `QUEUE`.
- **Missing:** a comment previously observed is absent from a complete sync of its post. State becomes `MISSING_FROM_SOURCE`. One absence is not proof of deletion.
- **Deleted upstream (absence):** absent from two consecutive complete syncs. State becomes `DELETED_UPSTREAM` with `deletion_evidence = ABSENT_TWICE`, and the purge rule in `PRIVACY-AND-BOUNDARIES.md` applies (ADR-009).
- **Deleted upstream (placeholder):** the source returns a known comment in the exact known placeholder shape (DEV: the observed key set with `user` equal to an empty object). State becomes `DELETED_UPSTREAM` at once, with `deletion_evidence = SOURCE_PLACEHOLDER`. The node stays in the thread so replies keep their parent, and the purge rule applies.
- **Placeholder without prior observation:** create the Comment directly in `DELETED_UPSTREAM` with `deletion_evidence = SOURCE_PLACEHOLDER`, no body stored, and authorship `UNKNOWN`.
- **Unexpected shape:** a node that is authorless in any other way, or has unknown keys, is not classified as a placeholder. The sync records a limitation, a friction entry is written, and the comment's lifecycle state is left unchanged until the shape is understood.
- **Purged:** body text and raw payloads removed; identifiers, lifecycle history, and non-content judgments remain.

#### Placeholders are structure only

A `DELETED_UPSTREAM` comment with `deletion_evidence = SOURCE_PLACEHOLDER` exists only as thread structure. It is excluded from classification, priority assignment, review queues, evaluation sets, and every count or metric.

#### Count reconciliation

When a sync compares observed comments with a source-reported count, it compares live comments only. DEV's `comments_count` excludes placeholders. Any remaining difference is recorded as a SyncRun limitation.

### PlatformIdentity

A platform-local identity. It is not a real-world Person.

- `platform_identity_id`
- `platform`
- `source_user_id`
- `handle`
- `display_name`
- `profile_url`
- `last_observed_at`

V1 stores only what arrives with comments. No profile lookups.

## Interpretation

### Classification

A model interpretation of a comment. Never part of the comment itself.

- `classification_id`
- `comment_id`
- `comment_source_record_id` (exactly which version was classified)
- `taxonomy_version`
- `primary_class`
- `flags` (list)
- `confidence` (value state)
- `explanation`
- `model_provider`, `model_id`
- `prompt_version`
- `input_fields_sent` (for the model boundary record)
- `classified_at`
- `outcome` (`OK`, `MALFORMED`, `FAILED`)

### PriorityAssignment

The policy's output. Separate from Classification so that policy can change without reclassifying.

- `priority_assignment_id`
- `comment_id`
- `classification_id` (nullable when classification failed)
- `policy_version`
- `tier` (`SURFACE`, `QUEUE`, `COLLAPSED`)
- `rule_applied` (class default or named override)
- `assigned_at`

## Human records

### EvaluationLabel

Ground truth for the corpus. Separate from operational overrides.

- `label_id`
- `comment_id`
- `corpus_version`
- `corpus_set` (`dev`, `test`, `adversarial`; `test` is prospective, ADR-010)
- `label_guide_version`
- `taxonomy_version`
- `primary_class`
- `flags`
- `consequential_prospective` (0 to 3)
- `consequential_retrospective` (0 to 3, value state)
- `context_reconstructed` (boolean)
- `replied_before_labeling` (boolean; the author's direct reply to the comment existed in the snapshot when it was labeled)
- `reason`
- `pass` (`initial`, `self_agreement`)
- `snapshot_run_id` (the sync or probe run the comment and its context were read from; provenance, not identity)
- `batch_id` (labeling batch; batch start and end times are recorded with the batch)
- `duration_seconds` (time from the comment being shown to the label being saved)
- `labeled_at`

### HumanOverride

Operational correction during review.

- `override_id`
- `comment_id`
- `classification_id` and `priority_assignment_id` being overridden
- `human_class` (optional)
- `human_tier` (optional)
- `notes`
- `overridden_at`

### ReviewEvent

Instrumentation for evaluation. Local only.

- `review_event_id`
- `comment_id` (nullable for group events)
- `event_type` (`SEEN`, `EXPANDED_GROUP`, `COLLAPSED_GROUP`, `OPENED_CONTEXT`, `BATCH_START`, `BATCH_END`)
- `condition` (`B0`, `B1`, `B2`, `OPERATIONAL`)
- `occurred_at`

### Disposition

What the author chose to do, or what the source shows they did.

- `disposition_id`
- `comment_id`
- `action` (`REPLIED`, `NO_REPLY_NEEDED`, `INVESTIGATE`, `SAVE`, `PROPAGATE`, `DEFER`)
- `origin` (`HUMAN`, `INFERRED_FROM_SOURCE`)
- `evidence_comment_id` (for inferred `REPLIED`: the author's reply)
- `action_at`
- `notes`

An inferred `REPLIED` never overwrites a human disposition. Both remain visible.

### PropagationEvent

Consequences beyond the conversation.

- `propagation_id`
- `comment_id`
- `kind` (see `SCOPE.md` propagation list)
- `target_type`
- `target_reference`
- `description`
- `recorded_at`

## Identity model

V1 uses `PlatformIdentity` only. Cross-platform `Person` resolution is deferred.

If introduced later, a Person must be separate from PlatformIdentity, and identity edges must carry evidence and review state. Similar handles never silently establish equivalence.

## Provenance rule

Every normalized record traces to source evidence. Every interpretation traces to the model, prompt, taxonomy, and policy versions that produced it. Every human judgment remains separately visible, and nothing derived ever overwrites it.
