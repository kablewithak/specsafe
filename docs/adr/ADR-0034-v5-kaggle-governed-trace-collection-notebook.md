# ADR-0034: Governed Kaggle Trace-Collection Notebook and Export Boundary

- **Status:** Accepted
- **Date:** 2026-07-08
- **Decision owner:** SpecSafe
- **Depends on:** ADR-0033

## Context

The retained Kaggle preflight pass authorizes implementation of the next boundary: a governed, fixed, public-safe trace-collection notebook.

The preflight pass does not justify ad hoc prompts, unrestricted generations, calibration fitting, policy evaluation, benchmarking, or publication. The collection boundary must preserve a narrow, inspectable route from a fixed self-authored prompt corpus to minimized trace records and a hash-addressed archive.

## Decision

Adopt `specsafe_v5_qwen_trace_collection.ipynb` as the only approved first Kaggle trace-collection notebook.

The notebook:

- requires `GPU T4 x2`, Internet, the retained preflight lineage, and a merged source commit SHA;
- uses six self-authored public-safe prompts across `structured_text`, `code`, and `open_ended_chat`;
- uses pinned Qwen revisions and greedy next-token blocks of at most four positions;
- exports runtime-candidate records and target-derived expected-outcome records to separate JSONL files;
- exports prompt hashes and token counts rather than raw prompt text, decoded candidate strings, or full logits;
- writes a manifest with source/preflight/corpus lineage and file hashes;
- creates one write-once archive for attempt 001;
- writes a bounded result JSON on success or failure;
- prohibits calibration, threshold setting, policy evaluation, policy comparison, capacity measurement, performance benchmarking, and publication.

## Target-derived label semantics

`target_argmax_matches_candidate` is a **greedy reference-match label**: whether the target model's next-token argmax equals the draft model's candidate token at the same prefix.

It is not a proof of exact speculative-decoding acceptance, losslessness, target-distribution preservation, or production serving behavior.

## Consequences

A successful run produces a small environment-specific Kaggle export suitable only for later local schema validation and governed split assignment.

No public dataset or replay release is authorized by this ADR.
