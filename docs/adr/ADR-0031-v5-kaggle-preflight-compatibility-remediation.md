# ADR-0031: Correct the Kaggle Qwen Preflight Compatibility Gates

- **Status:** Accepted
- **Date:** 2026-07-08
- **Decision owner:** SpecSafe
- **Depends on:** ADR-0029 and ADR-0030
- **Supersedes:** None

## Context

The first retained Kaggle preflight attempt used the approved Qwen pair under the source commit recorded in the retained evidence artifact. It resolved both immutable model revisions but stopped before tokenizer qualification and logits access.

The retained failure showed two implementation/environment facts:

```text
Kaggle GPU=Tesla P100-PCIE-16GB
active GPU architecture=sm_60
installed PyTorch CUDA build supports=sm_70 and newer
transformers=5.0.0
Qwen2Tokenizer lacks=additional_special_tokens_ids
```

The original notebook treated the tokenizer API assumption as an unexpected failure and did not classify GPU architecture compatibility before model qualification. No traces were collected.

## Decision

Amend the preflight notebook with two explicit compatibility gates before any trace collection is eligible.

1. Derive additional special-token IDs from `additional_special_tokens` through `convert_tokens_to_ids`. Do not depend on `additional_special_tokens_ids`, which is not available on the observed Qwen2 tokenizer/runtime combination.
2. Require the active Kaggle GPU architecture to appear in the installed PyTorch build's declared CUDA architectures. Fail with `gpu_architecture_unsupported` before model-hub activity when the accelerator cannot execute the installed PyTorch CUDA build.

The remediation run must use Kaggle **GPU T4 x2**. The previous P100 result remains retained as failed preflight evidence and is not overwritten or relabelled as a tokenizer-compatibility result.

## Consequences

The next Kaggle run is still qualification only. It may prove revision pinning, tokenizer identity, and finite logits access. It may not collect traces, benchmark performance, publish a dataset, or make a production claim.

A failure after this correction must be retained and diagnosed from its bounded JSON output. The model pair remains provisional until the preflight passes.
