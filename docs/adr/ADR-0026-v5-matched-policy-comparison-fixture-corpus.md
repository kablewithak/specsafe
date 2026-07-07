# ADR-0026: Freeze the V5 Matched Synthetic Policy-Comparison Fixture Corpus

- **Status:** Accepted
- **Date:** 2026-07-07
- **Decision scope:** Controlled synthetic development and adversarial-regression replay inputs
- **Related decisions:** ADR-0018, ADR-0020, ADR-0021, ADR-0022, ADR-0023, ADR-0024, ADR-0025

## Context

SpecSafe now has the minimum mechanics required for a case-level matched comparison:

- valid fixed-length and static-threshold baselines with normalized configuration identity;
- versioned synthetic capacity profiles;
- a retained V5 calibration artifact eligible for controlled policy research;
- a calibrated causal load-aware policy that uses only `CausalSchedulerContext`;
- a shared synthetic utility scorer; and
- a harness that compares valid policies on identical inputs while retaining the unsafe retrospective control as causally invalid.

The harness needs a governed corpus with explicit diagnostic cases. Reusing the frozen V5 calibration or final-evaluation corpus would either blur evidence roles or risk turning held-out material into policy-development input. A new, separate corpus is therefore required.

## Decision

Create `data/fixtures/synthetic_matched_policy_comparison_v1/` as a hash-addressed, self-authored fixture set with:

```text
fixture_set_id=synthetic-matched-policy-comparison-v1
fixture_set_version=1.0.0
evidence_class=synthetic_controlled
authorized_splits=development, adversarial_regression
```

The corpus contains six bounded diagnostic cases:

| Case | Profile | Split | Purpose |
|---|---|---|---|
| `MPC5-101` | `flat_capacity_control` | development | Neutral control when synthetic marginal verification cost is flat and low. |
| `MPC5-102` | `light_load` | development | Neutral control when extra verification is inexpensive. |
| `MPC5-103` | `moderate_load` | development | Retained adaptive-loses case. |
| `MPC5-104` | `saturated_load` | development | Constrained-capacity pruning diagnostic. |
| `MPC5-105` | `jagged_capacity` | development | Capacity-discontinuity stress diagnostic. |
| `MPC5-106` | `flat_capacity_control` | adversarial_regression | Unsafe retrospective look-ahead remains causal-fail and excluded. |

Each logical case has exactly two separately hashed artifacts:

```text
runtime input
expected outcomes
```

Runtime inputs are label-free. Expected outcomes remain post-hoc scoring material only.

## Constraints

- The corpus is not calibration material and must never refit the retained V5 calibrator.
- The corpus is not final held-out evaluation material and must not be used to create a final promotion claim.
- The corpus must not be rebalanced, altered, removed, or extended after governed comparison execution begins in order to improve a result.
- All policy comparisons must name the capacity profile declared by the case contexts.
- Case-level result categories are diagnostic only. They are not a global winner, promotion, deployment, throughput, latency, cost, or production claim.
- Unsafe retrospective outputs remain causal-fail, evaluation-only, and excluded from valid scores.

## Consequences

### Easier now

- The matched harness can be exercised against immutable on-disk inputs rather than in-memory test objects.
- Later comparison reports can retain neutral, adaptive-loses, adaptive-higher-under-declared-synthetic-conditions, and invalid-control examples.
- The repository has explicit evidence that synthetic capacity conditions are not assumed to produce one universal policy winner.

### Harder now

- Fixture changes require manifest/hash updates and review.
- The cases cannot be casually edited after a result is inspected.

### Non-claims

This corpus does not establish a policy advantage, serving throughput, latency reduction, cost reduction, real capacity behavior, Kaggle evidence, or production readiness.
