# ADR-0024: Add the V5 Calibrated Causal Load-Aware Policy Contract

- **Status:** Accepted
- **Date:** 2026-07-07
- **Decision scope:** Local synthetic replay policy contract only

## Context

V5 retained one bounded-monotone-beta calibration artifact after its frozen held-out
calibration assessment passed the calibration-eligibility gate. That assessment authorizes
controlled causal-policy research, not runtime control, throughput claims, policy utility
claims, or production promotion.

PR #88 added versioned synthetic capacity profiles. PR #89 retained normalized identity for
the fixed-length and static-threshold capacity-blind baselines. PR #90 added one shared
synthetic policy-utility scorer. The next missing boundary is the adaptive policy itself.

The adaptive policy must not:

- receive labels, observed outcomes, future tokens, retrospective prefixes, or replay results;
- refit or modify the retained V5 calibration artifact;
- use a profile other than the declared, hash-addressed synthetic profile;
- silently run when calibration authorization is absent;
- claim a winner, runtime control eligibility, throughput, latency, cost reduction, or
  production suitability.

## Decision

Add `CalibratedCausalLoadAwarePolicy` as a strict, replay-evaluation-only policy.

In calibrated research mode, the constructor requires:

1. the exact `CalibratedCausalLoadAwarePolicyConfig` contract;
2. a label-free V5 authorization contract pinned to the retained assessment and artifact
   SHA-256 values;
3. the exact retained `V5BoundedMonotoneBetaCalibrationArtifact` object whose canonical
   bytes match the authorized SHA-256;
4. the exact `SyntheticCapacityProfile` object matching the configuration's profile
   identity and configuration hash.

At decision time, the policy accepts only the existing exact `CausalSchedulerContext`.
It computes:

```text
calibrated_confidence = retained_v5_transform(lawful_conditional_survival_confidence)
expected_marginal_utility =
  calibrated_confidence × accepted_admission_value_units
  - marginal_verification_cost_units × marginal_verification_cost_weight
```

The policy emits:

- `ADMIT` when expected marginal utility is at least the configured minimum;
- `STOP` when it is lower;
- `CONSERVATIVE_FALLBACK` when explicitly configured in fallback mode.

Fallback mode accepts no active calibrator or capacity-profile dependency. It is causal and
terminal, but it is not an adaptive policy-improvement claim.

## Consequences

### Enabled

- One inspectable causal adaptive policy exists for later controlled replay.
- Each policy configuration retains deterministic hashes for its own configuration, the
  retained calibration artifact, and its capacity profile.
- The policy reacts to capacity only through its declared synthetic profile and the
  decision-time `CapacitySnapshot`.
- Causal guard failures, artifact drift, profile drift, and profile/snapshot mismatch fail
  explicitly.

### Deliberately not enabled

- No fixed-versus-threshold-versus-adaptive comparison report.
- No winner selection or policy ranking.
- No final-evaluation policy scoring.
- No threshold tuning, calibration refit, capacity-curve tuning, or mutation of V5 evidence.
- No claim that the policy improves verification utility under any workload.
- No runtime, serving, latency, throughput, cost, Kaggle, or production claim.

## Validation requirements

The merge gate requires focused tests for:

- exact retained-artifact verification;
- exact profile-reference verification;
- light-load admit and saturated-load stop behavior using the same lawful confidence;
- causal rejection of retrospective contexts;
- conservative fallback with no active dependencies;
- strict configuration validation and deterministic configuration hashing.

The full local suite, Ruff, format checks, diff checks, and frozen V5 evidence hash checks
remain required before merge.

## Next safe boundary

The next boundary is not a winner claim. It is a governed matched replay-comparison harness
that runs fixed-length, static-threshold, calibrated adaptive, and unsafe retrospective
control paths on identical immutable inputs and profiles, while preserving valid, neutral,
losing, and invalid results separately.
