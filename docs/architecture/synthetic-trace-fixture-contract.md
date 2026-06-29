# Synthetic Trace Fixture Contract

## Purpose

Phase 2 fixtures provide immutable, local, synthetic evidence for later verification-policy
replay. They are not model outputs, live-serving logs, production throughput evidence, or
calibration results.

## Structural boundary

Each logical case is split into two hash-addressed JSON artifacts:

```text
inputs/<case-id>.json
expected_outcomes/<case-id>.json
```

`inputs/` contains only `CausalSchedulerContext` values that a valid runtime scheduler may
receive. It excludes current candidate token IDs, future candidate token IDs, observed
acceptance labels, prefix-survival labels, and retrospective optimal-prefix information.

`expected_outcomes/` contains post-hoc candidate-token and survival labels. The loader may
combine the two artifacts into `SyntheticTraceReplayCase` for deterministic scoring only.
Future scheduling code must accept `CausalSchedulerContext` rather than a replay case or an
outcome object.

## Manifest rule

`manifest.json` lists every artifact with:

- case ID and split;
- runtime-input or expected-outcome role;
- synthetic data-role and source declaration;
- SHA-256 hash and byte count.

The loader rejects a missing file, hash mismatch, schema error, provenance mismatch, or
runtime/outcome alignment failure with a machine-readable failure code.

## Current fixture boundary

The fixture set contains four self-authored, token-ID-only cases:

- high-confidence light-load development case;
- low-confidence saturated-load development case;
- adversarial regression case reserved for later unsafe look-ahead control;
- final-evaluation case reserved from policy configuration changes.

The final-evaluation case is present to establish the split boundary. It is not evidence of a
policy result until a governed replay comparison is implemented in a later phase.

## Non-claims

This fixture set proves only that SpecSafe can load and validate versioned synthetic replay
inputs without routing evaluation labels into a runtime context. It does not prove confidence
calibration, adaptive-policy utility, real model behavior, Kaggle behavior, throughput, or
production readiness.
