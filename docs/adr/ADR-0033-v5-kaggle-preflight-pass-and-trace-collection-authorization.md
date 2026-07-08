# ADR-0033: Retain Successful Kaggle Preflight and Authorize Governed Trace-Collection Implementation

- **Status:** Accepted
- **Date:** 2026-07-08
- **Decision owner:** SpecSafe
- **Depends on:** ADR-0029, ADR-0030, ADR-0031, and ADR-0032

## Context

SpecSafe retained two failed Kaggle qualification attempts before a successful third attempt. The retained failures remain useful because they show the preflight stopped before trace collection when the GPU/runtime or notebook assumptions were not fit.

The successful third attempt used a Tesla T4 (`sm_75`) and source commit:

```text
061f58cba075cafbfbc4ed5d0afe9e817997a877
```

The retained result establishes:

```text
preflight_status=passes_kaggle_preflight
trace_collection_allowed=true
trace_collection_performed=false
failure=null
```

It also establishes, for both approved Qwen models:

- exact tokenizer class, vocabulary, token-to-ID mapping, special-token, and fixed self-authored probe compatibility;
- finite logits access;
- model-output vocabulary width equal to `model.config.vocab_size`;
- all probe token IDs inside the observed output vocabulary range;
- a Kaggle runtime whose Tesla T4 architecture is supported by the installed PyTorch build.

The passing preflight is retained under `attempt-003-t4-pass-result.json`. It does not invalidate, overwrite, or erase attempts 001 and 002.

## Decision

Retain all three preflight attempts in one versioned attempt registry.

Authorize the next repository slice only:

```text
governed_trace_collection_notebook_implementation
```

The next notebook must collect a small fixed self-authored corpus under the retained Qwen model revisions and exact environment/provenance controls. It must remain separate from the local synthetic policy corpus and from any public release asset.

This ADR does **not** authorize manual trace collection yet. The trace-collection contract, notebook, output schema, manifest protocol, failure handling, and static regression tests must first be committed and reviewed.

## Consequences

The project can now proceed from model-pair qualification to a governed trace-collection notebook implementation.

The following remain prohibited until later evidence gates pass:

- collecting ungoverned or ad hoc prompts;
- private, customer, or otherwise restricted data;
- final-policy evaluation or calibration fitting on Kaggle outputs;
- publishing a Hugging Face dataset or Space;
- throughput, latency, cost-saving, serving-capacity, or production claims.
