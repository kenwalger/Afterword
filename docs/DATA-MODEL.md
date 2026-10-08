# Data Model

**Version:** 13 (2026-10-08)

v13 (2026-10-08, later the same day) records that the purge also redacts saved probe runs, outside the store (ADR-009, amended 2026-10-08). The store's records are unchanged.

v12 (2026-10-08, later the same day) adds `ai_self_disclosed` to EvaluationLabel (`lg-v0.6`), and records the platform AI-disclosure value as a dormant observation, not stored. Nothing earlier is removed.

v11 (2026-10-08, later the same day) adds `read_via_translation` to EvaluationLabel (`LABELING-GUIDE.md` `lg-v0.5`). Nothing earlier is removed.

v10 (2026-10-08) adds `model_options` to Classification and its cache key (store schema 2), after the local context size changed. Nothing earlier is removed.

v9 (2026-10-07, ADR-009 amended) matches the deletion placeholder by its distinguishing features and ignores an allowlist of platform-wide keys. Nothing earlier is removed.

v8 (2026-10-04, `tax-v0.2`) records `CONTAINS_CODE` and `CONTAINS_LINK` as structural flags in `flags_by_source`. Nothing earlier is removed.

v7 (2026-10-04, with 150 `dev` labels recorded) adds the `calibration` value of EvaluationLabel `pass` and states which label analysis uses (`LABELING-GUIDE.md` `lg-v0.3`). Nothing earlier is removed.

v6 (2026-10-03, before any label or stored record existed) adds `sample_kind` to EvaluationLabel, so future label sources fit without migration (every V1 label is `researcher`); and, from the first implementation of the store, `LifecycleEvent`, `consecutive_absences` and `current_payload_hash` on Comment, `current_payload_hash` on ContentItem, and `error` on Classification.

v5 (2026-10-03, before any classification or stored record existed) adds `PlatformConnection` (ADR-013), edit detection by normalized text, the classification cache key, and the fields needed to trace a classification to its provider, model digest, pre-check, and normalization versions. Nothing earlier is removed.

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

### PlatformConnection

One configured connection to a source platform (ADR-013, rule 3). The content author, credentials, and settings belong to a connection, never to a module-level constant.

- `connection_id` (UUID)
- `platform`
- `account_source_user_id` (the platform's ID for the connected account, read from the source; DEV: `/api/users/me`)
- `created_at`

Credentials are not stored here or anywhere in the store. For DEV the key is read from the environment by the adapter (ADR-006). Who wrote a post comes from the post itself; the connection's account is the fallback when a post does not say.

### SyncRun

One execution of the source adapter.

- `sync_run_id`
- `connection_id`
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
- `connection_id`
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
- `body_text_hash` (SHA-256 of `body_text`; compared only between texts of the same `normalization_version`)
- `created_at`
- `updated_at` (value state)
- `first_observed_at`
- `last_observed_at`
- `lifecycle_state` (`ACTIVE`, `EDITED`, `MISSING_FROM_SOURCE`, `DELETED_UPSTREAM`, `PURGED`)
- `deletion_evidence` (value state: `ABSENT_TWICE`, `SOURCE_PLACEHOLDER`, or `NOT_YET_INTERPRETED` while not deleted)
- `current_source_record_id`
- `current_payload_hash` (hash of the current SourceRecord's payload, so an unchanged payload needs no lookup)
- `consecutive_absences` (complete syncs of its post in a row that did not return it; two means deleted)

#### Lifecycle rules

- **Edited:** the normalized text of a known comment changes. Both texts are produced by the same `normalization_version` (the earlier one is renormalized from its stored source body if the version changed). State becomes `EDITED`, a new SourceRecord is stored, classification is rerun, and the priority policy raises the comment to at least `QUEUE`.
- **Payload changed, text unchanged:** the payload hash changes but the normalized text does not (for example, a change in the source's HTML rendering). A new SourceRecord is stored for provenance; the lifecycle state does not change and nothing is reclassified.
- **Missing:** a comment previously observed is absent from a complete sync of its post. State becomes `MISSING_FROM_SOURCE`. One absence is not proof of deletion.
- **Deleted upstream (absence):** absent from two consecutive complete syncs. State becomes `DELETED_UPSTREAM` with `deletion_evidence = ABSENT_TWICE`, and the purge rule in `PRIVACY-AND-BOUNDARIES.md` applies (ADR-009).
- **Deleted upstream (placeholder):** the source returns a known comment in the placeholder shape (DEV, ADR-009 as amended 2026-10-07: `user` equal to an empty object, the body replaced with the placeholder text, `id_code`, `created_at`, and `children` kept, and every key of the first observed placeholder present; keys on the allowlist of platform-wide fields, initially `ai_disclosure_label` and `ai_disclosure_level`, are ignored). State becomes `DELETED_UPSTREAM` at once, with `deletion_evidence = SOURCE_PLACEHOLDER`. The node stays in the thread so replies keep their parent, and the purge rule applies.
- **Placeholder without prior observation:** create the Comment directly in `DELETED_UPSTREAM` with `deletion_evidence = SOURCE_PLACEHOLDER`, no body stored, and authorship `UNKNOWN`.
- **Unexpected shape:** a node that is authorless in any other way, or has keys outside the known set and the platform-wide allowlist, is not classified as a placeholder. Adding a key to the allowlist needs evidence recorded in the friction log. The sync records a limitation, a friction entry is written, and the comment's lifecycle state is left unchanged until the shape is understood.
- **Purged:** body text and raw payloads removed; identifiers, lifecycle history, and non-content judgments remain.

#### LifecycleEvent

Every change of `lifecycle_state`, kept after any purge: `event_id`, `comment_id`, `sync_run_id`, `from_state`, `to_state`, `reason` (such as `first_observed`, `text_changed`, `absent`, `source_placeholder`, `purge`), `occurred_at`.

The purge runs in the same ingest that detects the deletion, which is no later than ADR-009's "at the next sync". A comment deleted after it was observed ends `PURGED`; a placeholder first observed without content stays `DELETED_UPSTREAM`, since nothing was held to purge. Model text derived from the comment (`raw_output`, `explanation`) is purged with it; class, flags, and tiers remain as non-content judgments. The same ingest redacts the comment in the saved probe runs on disk, which are not part of the store (ADR-009, amended 2026-10-08).

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
- `flags_by_source` (which flags came from the model, from structure (`REPLY_TO_AUTHOR`, and from `tax-v0.2` `CONTAINS_CODE` and `CONTAINS_LINK`, set from the comment's normalization for B1 and B2 alike), and from the deterministic pre-check)
- `confidence` (value state; `LOW`, `MEDIUM`, or `HIGH` when `PRESENT`; `NOT_EXPOSED` for a heuristic)
- `explanation`
- `classifier_kind` (`HEURISTIC` for B1, `MODEL` for B2 and secondary models)
- `model_provider`, `model_id` (for a heuristic: `afterword` and the heuristic version, such as `hb-v0.1`)
- `model_digest` (value state; the local model's content digest, which pins it; `NOT_EXPOSED` for a remote model, which is pinned by its dated ID)
- `prompt_version` (null for a heuristic; `classifier_kind` says why)
- `model_options` (part of the cache key; see Cache below)
- `normalization_version`
- `precheck_version`
- `input_fields_sent` (for the model boundary record)
- `input_hash` (SHA-256 of the canonical serialization of everything sent to the classifier)
- `raw_output` (the provider's response text, kept locally for diagnosing malformed results; purged with the comment's body)
- `latency_ms`
- `classified_at`
- `outcome` (`OK`, `MALFORMED`, `FAILED`)
- `error` (a category only, such as `malformed:not_json` or `failed:timeout`; never a message that could hold a host name or path)

#### Cache and incremental classification

A classification is identified by its **cache key**: `input_hash`, `model_provider`, `model_id`, `model_digest`, `prompt_version`, `taxonomy_version`, and `model_options` (from 2026-10-08: the generation options that can change the answer, such as `num_ctx=4096;num_predict=200;seed=20261003;temperature=0` for Ollama; null for a heuristic. Rows from before store schema 2 record the options they ran with, 2048-token context for Ollama). The input hash covers the comment's normalized text and every context field sent with it (post title, parent comment text), so an edit to a parent changes the key.

A comment is classified only when no `OK` or `MALFORMED` classification exists for its current key: new comments, edited comments (or edited context), and any version change. `MALFORMED` is kept rather than retried, because at temperature 0 the same input produces the same output. `FAILED` (transport error, timeout) is retried on the next run.

### PriorityAssignment

The policy's output. Separate from Classification so that policy can change without reclassifying.

- `priority_assignment_id`
- `comment_id`
- `classification_id` (nullable when classification failed)
- `policy_version`
- `tier` (`SURFACE`, `QUEUE`, `COLLAPSED`)
- `rule_applied` (class default or named override; the rule that decided the tier, see `PRIORITY-POLICY.md`)
- `rules_fired` (every rule whose condition held, in policy order)
- `assigned_at`

## Human records

### EvaluationLabel

Ground truth for the corpus. Separate from operational overrides.

- `label_id`
- `comment_id`
- `corpus_version`
- `corpus_set` (`dev`, `test`, `adversarial`; `test` is prospective, ADR-010)
- `sample_kind` (who produced the label and how the comment was sampled; `researcher` for every V1 label. Future sources are described in `LABELING-AT-SCALE.md` and get their own values; random and targeted samples are never mixed in one measure, see `EVALUATION.md`)
- `label_guide_version`
- `taxonomy_version`
- `primary_class`
- `flags`
- `consequential_prospective` (0 to 3)
- `consequential_retrospective` (0 to 3, value state)
- `context_reconstructed` (boolean)
- `replied_before_labeling` (boolean; the author's direct reply to the comment existed in the snapshot when it was labeled)
- `read_via_translation` (boolean, from `lg-v0.5`; the labeler read the comment through a translation. Absent on earlier labels, which means "not recorded")
- `ai_self_disclosed` (boolean, from `lg-v0.6`; the comment says explicitly that an AI wrote it, as recorded by the labeler. Never inferred. Absent on earlier labels, which means "not recorded")
- `reason`
- `pass` (`initial`, `calibration`, `self_agreement`; a calibration label re-labels a comment from scratch and never overwrites its initial label. Analysis uses the latest label from a pass other than `self_agreement`, `LABELING-GUIDE.md`)
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
