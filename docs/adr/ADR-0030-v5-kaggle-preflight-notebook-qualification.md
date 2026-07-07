# ADR-0030: Implement the V5 Kaggle Qwen Preflight Notebook Qualification Gate

- **Status:** Accepted for Kaggle qualification only
- **Date:** 2026-07-08
- **Decision owner:** SpecSafe
- **Depends on:** ADR-0028 and ADR-0029
- **Supersedes:** None

## Context

ADR-0029 selects a provisional Qwen2.5 base model pair:

```text
draft_model_id=Qwen/Qwen2.5-0.5B
target_model_id=Qwen/Qwen2.5-1.5B
```

Selection alone does not prove that the pair has identical token space, that resolved revisions can be pinned, or that logits are available in the Kaggle environment.

The first Kaggle execution must therefore qualify the experimental boundary before any trace collection. It must preserve failure evidence rather than silently switching models or proceeding after a partial pass.

## Decision

Commit one self-contained Kaggle notebook:

```text
notebooks/kaggle/specsafe_v5_qwen_preflight.ipynb
```

The notebook shall:

1. Require an explicit merged SpecSafe source commit SHA.
2. Require a Kaggle GPU.
3. Require `transformers >= 4.37.0`.
4. Resolve each model repository to an immutable Hugging Face commit SHA through `HfApi.model_info`.
5. Load both tokenizers at those exact revisions with `trust_remote_code=False`.
6. Compare tokenizer classes, full token-to-ID mappings, vocabulary sizes, special-token maps/IDs, and six self-authored fixed probes.
7. Stop before model loading if tokenizer compatibility fails.
8. Load one model at a time and verify a finite logits forward pass without retaining logits.
9. Write a canonical machine-readable result to:

```text
/kaggle/working/specsafe_v5_qwen_preflight_result.json
```

10. Stop after qualification. It must not collect traces.

## Safety and privacy controls

- No Hugging Face token, Kaggle secret, API key, environment dump, private prompt, customer input, or raw model payload is retained.
- Only self-authored tokenizer probes are used; the stored result retains their SHA-256 values and token counts, not their raw text or token IDs.
- `trust_remote_code=False` is required for tokenizer and model loading.
- The notebook writes a bounded failure record before raising an error.

## Consequences

A successful output authorizes only the next governed trace-collection slice. It does not authorize a dataset publication, public replay release, production throughput claim, serving integration, or promotion of the adaptive policy.

A failed output must be retained and reviewed. A replacement model pair requires a new ADR.
