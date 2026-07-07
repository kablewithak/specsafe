# V5 Matched Policy Comparison Corpus — Authoring Ledger

## Status

```text
fixture_set_id=synthetic-matched-policy-comparison-v1
fixture_set_version=1.0.0
evidence_class=synthetic_controlled
permitted_splits=development, adversarial_regression
policy_tuning_status=not_authorized
final_evaluation_status=not_authorized
```

This corpus is a self-authored diagnostic fixture set for testing the matched-comparison harness under predeclared synthetic configurations. It is not V5 calibration evidence, not V5 final held-out evidence, and not a serving benchmark.

## Locked diagnostic intent

| Case | Split | Profile | Intended diagnostic property |
|---|---|---|---|
| `MPC5-101` | development | flat capacity control | Valid-policy neutral control under low synthetic marginal cost. |
| `MPC5-102` | development | light load | Valid-policy neutral control under inexpensive synthetic verification. |
| `MPC5-103` | development | moderate load | Retained adaptive-loses control: threshold/fixed can retain more utility. |
| `MPC5-104` | development | saturated load | Retained constrained-capacity pruning control. |
| `MPC5-105` | development | jagged capacity | Discontinuity stress case for declared synthetic cost behavior. |
| `MPC5-106` | adversarial regression | flat capacity control | Unsafe retrospective look-ahead is deliberately causal-fail and excluded from valid scores. |

## Invariants

- Every logical case has one label-free runtime-input artifact and one post-hoc expected-outcome artifact.
- Runtime inputs contain no candidate tokens or observed outcomes.
- Expected outcomes are used only after decisions are retained by replay.
- Every context names exactly one declared synthetic capacity profile.
- The manifest hashes every fixture artifact.
- Case-level outcomes are diagnostic checks only. They do not constitute a global winner or promotion claim.
- No case may be added, removed, rebalanced, or modified to improve a result after governed comparison execution begins.

## Non-claims

This corpus does not establish policy superiority, production throughput, latency, cost reduction, serving capacity, or live-traffic behavior.
