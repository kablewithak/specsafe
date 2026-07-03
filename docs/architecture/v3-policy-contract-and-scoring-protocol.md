# V3 Policy Contract and Scoring Protocol

## Purpose

This document turns the V3 constitution into the contracts that later code must enforce. It keeps three things separate:

1. what the policy may know while deciding;
2. what the scorer may learn after decisions are recorded;
3. what a report is allowed to claim.

## V3 fixture root and split layout

All V3 evidence must live below this fresh root:

```text
data/fixtures/synthetic_verification_policy_v3/
```

Required layout:

```text
scenario_family_registry.json
calibration_manifest.json
final_evaluation_manifest.json
adversarial_regression_manifest.json

inputs/
  calibration/cases/V3CAL-###.json
  final_evaluation/cases/V3FINAL-###.json
  adversarial_regression/cases/V3ADV-###.json

expected_outcomes/
  calibration/cases/V3CAL-###.json
  final_evaluation/cases/V3FINAL-###.json
  adversarial_regression/cases/V3ADV-###.json
```

Runtime inputs and outcomes must remain physically separate.

## IDs and volumes

| Split | IDs | Cases | Candidate positions | Observations |
|---|---|---:|---:|---:|
| Calibration | `V3CAL-001` to `V3CAL-036` | 36 | 4 | 144 |
| Final evaluation | `V3FINAL-001` to `V3FINAL-024` | 24 | 4 | 96 |
| Adversarial regression | `V3ADV-001` to `V3ADV-008` | 8 | 4 | 32 |

No V3 case ID may reuse a V1 or V2 case ID.

## Runtime contract

A valid V3 policy receives a strict runtime object for one candidate position. It may contain only:

```text
trace_id
request_id
workload_type
split
scenario_family_id
decode_round
block_position_index
visible_prefix_token_ids
raw_confidence
capacity_profile_id
capacity_snapshot
calibration_fitness_state
```

The policy may receive its own earlier decision-path state only when that state is made entirely from prior lawful runtime values.

The runtime object must reject unknown fields.

## Outcome contract

The scorer receives a separate post-decision outcome object. It may contain:

```text
candidate_token_id
observed_acceptance
prefix_survival_label
outcome_provenance
```

The outcome object must never be passed to a valid runtime policy.

## Policy actions and reason codes

Valid V3 policies must emit exactly one of:

```text
ADMIT
STOP
CONSERVATIVE_FALLBACK
```

Minimum reason codes:

```text
fixed_length_limit
raw_threshold_not_met
calibrated_confidence_below_minimum
marginal_value_below_capacity_cost
maximum_prefix_length_reached
confidence_not_fit_for_automated_scheduling
```

The unsafe control may emit a separate invalid action only inside evaluation-only code. It must not share the valid runtime interface.

## Capacity profiles

Capacity is a declared replay cost, not a hidden production measurement.

All V3 synthetic profiles use this unit:

```text
normalized_marginal_verification_cost
```

The four fixed profiles are:

| Profile | Position 1 | Position 2 | Position 3 | Position 4 | Meaning |
|---|---:|---:|---:|---:|---|
| `light_load_v1` | 0.04 | 0.06 | 0.08 | 0.10 | Extra checking stays relatively cheap. |
| `moderate_load_v1` | 0.15 | 0.22 | 0.32 | 0.45 | Extra checking becomes progressively more expensive. |
| `saturated_load_v1` | 0.35 | 0.55 | 0.80 | 1.10 | Extra checking competes sharply for limited capacity. |
| `jagged_capacity_v1` | 0.10 | 0.70 | 0.20 | 0.90 | Uneven pressure tests brittle greedy decisions. |

The policy must read the current profile cost from the named profile. It may not infer a hidden cost from evaluation outcomes.

## Decision protocol

For each case, a policy is called in candidate-position order.

1. Validate the runtime object and its manifest membership.
2. Validate that the visible prefix length matches the candidate position.
3. Confirm that no outcome or future field is present.
4. Resolve the named capacity profile and its marginal cost for the current position.
5. Apply the policy's fixed rule.
6. Record the decision before reading any outcome.
7. Stop the case when the policy returns `STOP`, reaches its maximum length, or invokes the fallback's fixed length.
8. Only after the full decision trace is retained may scoring read outcomes.

## Adaptive-policy formula

For candidate position `k`:

```text
prefix_survival_estimate(k) = calibrated_confidence(1) × ... × calibrated_confidence(k)
expected_marginal_value(k) = prefix_survival_estimate(k)
net_marginal_value(k) = expected_marginal_value(k) - capacity_cost(k)
```

`causal-marginal-prefix-v1` admits position `k` only when:

```text
calibrated_confidence(k) >= 0.55
net_marginal_value(k) >= 0.05
k <= 4
```

It may use only prior lawful calibrated values to calculate earlier terms in the product.

## Scoring protocol

The scorer reads outcomes only after decisions are fixed.

For each case:

```text
admitted_positions = number of ADMIT actions
accepted_work = admitted positions that survive before the first observed rejection
verification_waste = admitted_positions - accepted_work
capacity_cost = sum(profile marginal cost for every admitted position)
realized_policy_utility = accepted_work - capacity_cost
```

For a full report, calculate:

- mean realized utility per case;
- mean admitted positions per case;
- mean accepted work per case;
- mean verification waste per case;
- action counts by policy;
- breakdown by workload type and capacity profile;
- raw and calibrated confidence quality;
- causal-safety result for every policy.

## Comparison validity rules

A comparison is valid only when all compared policies use the same:

```text
final-evaluation manifest hash
capacity profile ID
case slice
scorer version
utility formula version
```

A report must mark a comparison invalid when:

- a runtime policy sees an outcome or future-bearing field;
- a final manifest hash does not match;
- calibration fitting reads final files;
- an adaptive policy runs as probability-driven after calibration failure;
- policies are compared across different case or profile inputs without clear separation.

## Final-report language rules

A valid final report may say:

```text
Under these named synthetic replay conditions, this policy had an advantage, tie, loss, or fallback result.
```

It may not say:

```text
This policy is faster in production.
This policy saves real serving cost.
This policy works for all workloads.
```

## Next implementation boundary

The next engineering slice creates only the V3 registry, schema, loader, and empty path rules. It must not create V3 calibration cases, final-evaluation cases, outcomes, manifests, calibration fitting, or policy code.
