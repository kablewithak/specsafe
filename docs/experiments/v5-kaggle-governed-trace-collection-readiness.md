# V5 Governed Kaggle Trace-Collection Readiness

## Purpose

This document records the evidence boundary after the successful Kaggle Qwen preflight and before the trace-collection notebook is implemented.

## Retained qualification result

```text
preflight_id=v5-qwen-same-tokenizer-preflight-v1
attempt_id=attempt-003-t4-pass
preflight_status=passes_kaggle_preflight
source_commit_sha=061f58cba075cafbfbc4ed5d0afe9e817997a877
artifact_sha256=4b2e096ecf57e7c729918a83a6b84434ab0dc9dac094f6b9eadff40f84e7d9dd
trace_collection_allowed=true
trace_collection_performed=false
```

The passing model pair remains:

```text
draft_model_id=Qwen/Qwen2.5-0.5B
draft_revision=060db6499f32faf8b98477b0a26969ef7d8b9987
target_model_id=Qwen/Qwen2.5-1.5B
target_revision=8faed761d45a263340a0528343f099c05c9a4323
```

## What the pass proves

- The selected Kaggle T4 runtime can execute bounded finite-logits access for both pinned models.
- The two pinned models share an exactly compatible tokenizer boundary under the preflight checks.
- The next repository slice may implement a governed trace-collection notebook.

## What the pass does not prove

- Candidate trace quality.
- Acceptance or prefix-survival behavior.
- Calibration fitness.
- Policy utility.
- Throughput, latency, cost savings, or serving capacity.
- Public-dataset readiness or production readiness.

## Next notebook contract

The trace-collection notebook must be implemented before any new Kaggle execution. It must:

1. Use only a small fixed corpus of self-authored, public-safe prompts stored in the repository.
2. Pin the model revisions recorded above and reject revision drift.
3. Retain only minimized trace fields needed for later local replay and evaluation.
4. Separate runtime-visible trace fields from post-hoc labels.
5. Record environment metadata, package versions, seed, decoding configuration, prompt/case IDs, and a manifest with hashes.
6. Write bounded failure results before stopping on a validation failure.
7. Avoid raw private prompts, credentials, full logits, or sensitive payloads.
8. Stop after controlled trace export; it may not fit calibration, select policy thresholds, run policy comparisons, or publish output.

## Explicit authorization state

```text
governed_trace_collection_notebook_implementation_authorized=true
governed_trace_collection_execution_authorized=false
public_dataset_authorized=false
public_replay_release_authorized=false
policy_evaluation_authorized=false
runtime_control_eligible=false
```
