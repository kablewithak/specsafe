# ADR-0023: Add a Shared Synthetic Policy-Utility Scorer Before Adaptive Policy Work

- **Status:** Accepted
- **Date:** 2026-07-07
- **Decision scope:** Local synthetic replay scoring only

## Context

SpecSafe now has two normalized, valid, capacity-blind baseline policies and versioned
synthetic capacity profiles. It does not yet have an adaptive policy, a policy comparison
report, or evidence that any policy is better.

A later comparison needs one declared scoring method. Allowing each future policy to
calculate its own utility would couple policy logic to evaluation semantics, create
incomparable results, and invite post-hoc formula drift.

## Decision

Add `specsafe.eval_harness` with one strict shared scorer for an already-recorded
`ValidPolicyReplayResult`.

The initial formula is deliberately small and fixed by `PolicyUtilityScoringConfig`:

```text
policy_utility = accepted_admission_count × accepted_admission_value_units
                 − Σ(admitted marginal verification cost × marginal_cost_weight)
```

The scorer:

- accepts only exact typed fixture, replay, capacity-profile, and scoring-config objects;
- evaluates costs from the lawful runtime `CapacitySnapshot` retained in immutable fixture
  contexts;
- records profile/configuration/replay hashes with the resulting score;
- accepts only `development` and `adversarial_regression` splits in this slice;
- returns a non-comparative score with `no_cross_policy_winner_claim`;
- remains separate from policy execution, calibration fitting, and report generation.

## Consequences

### Easier now

- A future adaptive policy and the normalized baselines can use one scoring formula.
- Score artifacts retain input identities and hash-addressed provenance.
- Capacity-derived cost is inspectable per admitted decision.

### Deliberately not enabled

- No policy ranking or winner selection.
- No scoring of calibration or final held-out evidence.
- No policy configuration, threshold, capacity-curve, or calibrator tuning.
- No throughput, latency, cost-saving, or production claim.
- No adaptive scheduler.

## Guardrails

- Expected outcomes are used only because replay decisions already exist.
- The scorer cannot call a policy or change a decision.
- Unsafe retrospective replay objects are rejected by exact type.
- Frozen V5 calibration and final-evidence assets remain outside this slice.

## Next boundary

The next safe step after this scorer is the calibrated causal load-aware policy boundary.
That policy must consume only the approved causal runtime context, the retained V5
calibration artifact, and a declared synthetic capacity profile. A matched comparison
protocol may begin only after that policy is guarded and regression-tested.
