# V5 Kaggle Experiment Charter — Same-Tokenizer Trace Acquisition

## Status

```text
phase=Kaggle evidence acquisition
authorization_source=ADR-0028 Phase 5 gate
experiment_status=design locked; notebook not yet implemented
evidence_class_when_run=kaggle_measured
```

## Objective

Collect a small, deterministic, public-safe trace bundle from one predeclared draft/target model pair. The bundle must let SpecSafe test whether conclusions from controlled synthetic replay are directionally consistent with a documented Kaggle environment.

This experiment is evidence acquisition. It is not a production benchmark and it does not change the existing controlled synthetic comparison result.

## Selected provisional model pair

```text
draft_model_id=Qwen/Qwen2.5-0.5B
target_model_id=Qwen/Qwen2.5-1.5B
model_type=base causal language models
pair_status=requires immutable-revision and tokenizer preflight
```

## Why base models

The trace collector needs next-token logits, token IDs, and conditional probability data. Base models avoid introducing chat-template and post-training behavior into the first token-level collection experiment.

## Hard preflight gate

Trace collection may begin only if all conditions pass:

```text
- model source and license recorded;
- immutable target and draft revisions resolved;
- exact tokenizer compatibility proven;
- public-safe prompt corpus declared;
- no secrets printed or committed;
- environment metadata captured;
- deterministic seed/decode settings declared;
- output path is local/Kaggle working storage only;
- sanitized export schema validates before publication.
```

## Initial prompt corpus design

The first notebook must use self-authored, public-safe prompts only.

```text
corpus_id=specsafe-kaggle-pilot-prompts-v1
planned_prompt_count=24
workload_distribution:
  structured_text=8
  code=8
  open_ended_chat=8
```

The prompt corpus becomes a versioned asset in a later slice. It must not include private, client, user, or licensed-restricted text.

## Collection protocol

For each prompt:

1. Apply a fixed prompt-to-token policy.
2. Generate a fixed number of draft candidate positions.
3. Record the draft candidate token IDs and raw probabilities.
4. Evaluate the same candidate positions with the target model.
5. Record target probabilities and post-hoc conditional acceptance/survival labels.
6. Keep runtime-visible fields separate from post-hoc scoring fields.
7. Record timing only as Kaggle-environment metadata.
8. Emit sanitized JSONL plus a manifest and reproducibility record.

## Required retained metadata

```text
experiment_id
source_commit_sha
kaggle_notebook_revision
kaggle_accelerator_metadata
python_version
torch_version
transformers_version
cuda_version
draft_model_id
draft_model_revision
target_model_id
target_model_revision
tokenizer_id
tokenizer_revision
tokenizer_compatibility_result
seed
decoding_configuration_id
prompt_corpus_id
trace_schema_version
export_manifest_sha256
```

## Stop conditions

Stop immediately and retain a failure record if:
- tokenizers are not exactly compatible;
- model revisions cannot be pinned;
- logits/probabilities cannot be accessed;
- the prompt corpus is not public-safe;
- runtime fails before deterministic trace export;
- any output includes a secret, raw private prompt, or uncontrolled payload.

## Non-claims

This future Kaggle experiment will not prove:
- production throughput;
- production latency;
- DeepSeek or DSpark reproduction;
- live concurrency behavior;
- a universal policy advantage;
- production readiness;
- a public dataset release.

## Next implementation boundary

Implement the Kaggle notebook preflight and its machine-readable qualification result. No trace corpus collection begins until that preflight is retained and passes.
