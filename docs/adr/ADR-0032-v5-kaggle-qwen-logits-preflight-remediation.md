# ADR-0032: Correct Qwen Padded-Vocabulary Logits Qualification

- **Status:** Accepted
- **Date:** 2026-07-08
- **Decision owner:** SpecSafe
- **Depends on:** ADR-0029, ADR-0030, and ADR-0031

## Context

The second retained Kaggle preflight attempt ran on a compatible Tesla T4 (`sm_75`) and completed the full exact tokenizer-compatibility gate for the approved Qwen pair. It then failed on the first draft-model logits access check.

The retained result establishes:

```text
GPU=Tesla T4
GPU architecture=sm_75
PyTorch supports=sm_75
tokenizer compatibility=pass
trace collection performed=false
failure=logits_access_failed
```

The preflight implementation incorrectly required `logits.shape[-1] == len(tokenizer)`. That rule is too strict for a model whose output vocabulary may be padded beyond the tokenizer vocabulary. The attempt did not retain the observed logits width, model configuration vocabulary width, or finiteness state, so it cannot distinguish a padded-vocabulary condition from non-finite logits or an actual output mismatch.

The notebook also emitted a `torch_dtype` deprecation warning in the observed Transformers runtime.

## Decision

Amend the logits qualification gate.

A model passes logits qualification only when all of the following are true:

1. The logits tensor is rank three.
2. All logits are finite.
3. `logits.shape[-1] == model.config.vocab_size`.
4. `len(tokenizer) <= model.config.vocab_size`.
5. Every token ID in the fixed self-authored forward probe is inside the observed logits range.

A model output vocabulary larger than the tokenizer vocabulary is valid only when the above conditions hold.

The notebook must retain bounded diagnostics for both successful and failed logits checks: dtype, logits shape, observed output width, configured vocabulary width, tokenizer vocabulary size, maximum probe token ID, and finite status when available.

Use the current Transformers-compatible `dtype` load argument in place of the deprecated `torch_dtype` argument.

The notebook must also invoke the existing GPU architecture gate before contacting the model hub.

## Consequences

Attempt 002 remains retained as a failed preflight result. It is not overwritten or reclassified. The next run remains qualification only and must use a fresh Kaggle notebook configured with Internet enabled and GPU T4 x2.

No trace collection, benchmark, dataset publication, or production claim is authorized by this change.
