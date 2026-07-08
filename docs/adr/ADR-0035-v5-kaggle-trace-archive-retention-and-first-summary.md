# ADR-0035: V5 Kaggle Trace Archive Retention and First Summary

## Status
Accepted

## Context

The governed trace-collection notebook from PR #101 was executed once in Kaggle using the pinned Qwen model pair and the fixed self-authored prompt corpus.
The notebook final cell reported `passes_governed_trace_collection`, `failure_code=null`, `archive_created=true`, and `trace_collection_performed=true`.
The terminal result JSON was not retained because a Kaggle browser/session refresh removed `/kaggle/working` outputs before it could be downloaded.
The trace archive ZIP was downloaded before that refresh and is retained in this repository.

## Decision

Retain the trace archive as the authoritative attempt-001 evidence payload and explicitly document the missing terminal result JSON rather than recreating it manually or rerunning the notebook to backfill the envelope.

Retained archive:

```text
collection_id=v5-qwen-governed-trace-collection-v1
collection_attempt_id=attempt-001-t4
archive_sha256=03059b5ed15fdde07faff92cb9485cb89793e03e010fd8f43b8f674d17fdb81c
source_commit_sha=cff5905075044770010653c637d3c52c4ccb6fbe
preflight_attempt_id=attempt-003-t4-pass
```

The retained archive contains:

```text
runtime_records.jsonl
expected_outcomes.jsonl
manifest.json
```

## Rationale

The archive is the research payload. It contains the runtime records, the target-derived outcome records, and the provenance manifest with source commit, model revisions, environment, prompt-corpus hash, and file hashes.
The missing terminal result JSON was a convenience status envelope. Recreating it after the fact would weaken evidence integrity, and rerunning the notebook just to regenerate the envelope would create a second attempt while pretending it was the first.

## Consequences

- Attempt 001 is retained as a valid trace archive with a documented terminal-envelope gap.
- The repository can proceed to local trace analysis using the archive contents.
- Calibration refit, policy promotion, public release, throughput claims, latency claims, and production-readiness claims remain unauthorized.
- Future Kaggle notebooks should add an explicit post-run download reminder and optional notebook display links for every required output.

## First measured summary

The attempt contains 24 candidate positions across 6 self-authored cases.
Target argmax matched the draft candidate in 15 of 24 positions, a raw match rate of 0.625.
Mean draft probability was higher for matched candidates than non-matched candidates, but this is a small trace corpus and not yet a calibrated policy result.
