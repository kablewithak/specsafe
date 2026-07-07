# ADR-0029: Select and Preflight the V5 Kaggle Same-Tokenizer Model Pair

- **Status:** Accepted for controlled Kaggle preflight only
- **Date:** 2026-07-08
- **Decision owner:** SpecSafe
- **Depends on:** ADR-0028 Phase 5 gate
- **Supersedes:** None

## Context

The controlled synthetic Phase 5 gate authorizes a separate Kaggle evidence-acquisition phase. It does not authorize a serving benchmark, a production claim, or a public dataset release.

The Kaggle experiment must produce a small, reproducible, public-safe trace layer that can be exported into the existing local-first SpecSafe contracts. The core requirement is token-level comparability between a smaller draft model and a larger target model.

A model pair is unacceptable if:
- it has incompatible tokenizer/vocabulary behavior;
- revisions are not pinned;
- the license/source cannot be recorded;
- the notebook requires private prompts, secrets, or client data;
- the experiment silently changes model pair after a preflight failure;
- traces cannot be sanitized into the existing trace-contract boundary.

## Decision

Select this **provisional, preflight-gated** pair:

```text
draft_model_id=Qwen/Qwen2.5-0.5B
target_model_id=Qwen/Qwen2.5-1.5B
model_family=Qwen2.5 base
draft_parameter_count=0.49B
target_parameter_count=1.54B
license=Apache-2.0 for both model repositories
```

Both are base causal language models. This is deliberate: the Kaggle trace collector needs stable next-token logits and token IDs, not conversational quality or chat-template behavior.

The selection is not final until the notebook completes the preflight protocol below and records exact immutable revisions.

## Required preflight protocol

The notebook must resolve and record:
- model repository IDs;
- immutable commit revisions returned by the model hub;
- tokenizer repository/revision identifiers;
- `transformers`, `torch`, CUDA, and Python versions;
- Kaggle accelerator metadata;
- model dtypes/device mapping;
- seed and decoding configuration;
- license/source record.

The notebook must prove exact token-space compatibility before trace collection:

1. Load both tokenizers by the resolved immutable revisions.
2. Compare tokenizer class names.
3. Compare vocabulary sizes.
4. Compare complete token-to-ID mappings.
5. Compare special-token maps and all special token IDs.
6. Encode a fixed self-authored probe set and compare every token ID sequence.
7. Abort trace collection if any check fails.

A same-family label is not accepted as proof of tokenizer compatibility.

## Trace collection scope

This ADR authorizes only:
- public-safe, self-authored pilot prompts;
- target/draft next-token probability and candidate-trace collection;
- environment-specific timing observations;
- sanitized local export;
- explicit failure reports.

It does not authorize:
- live serving;
- CUDA/kernel work;
- model training;
- a production throughput claim;
- a public dataset release;
- use of client prompts, private prompts, personal data, secrets, or raw hidden reasoning data.

## Failure handling

```text
preflight failure
  -> record machine-readable failure
  -> retain environment/model metadata
  -> do not collect traces
  -> do not substitute another model pair without a new ADR
```

## Consequences

This pair keeps the first empirical experiment small and interpretable. It is expected to be feasible on a Kaggle GPU, but this ADR does not claim a specific hardware fit or runtime before measurement.

The model pair is an experimental evidence source. Any timing or capacity observation is Kaggle-environment specific and cannot be represented as production serving performance.
