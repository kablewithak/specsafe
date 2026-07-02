# V2 Bounded Platt Scaling Candidate Specification

## Status

```text
specification_status=selected_candidate_contract
fixture_set_id=synthetic-calibration-redesign-v2
candidate_artifact_id=bounded-platt-scaling-v1
candidate_artifact_version=1.0.0
implementation_status=not_started
fixture_authoring_status=not_authorized
fitting_status=not_authorized
final_evaluation_status=not_authorized
adaptive_policy_status=blocked
runtime_control_status=not_eligible
```

## Purpose

Specify the fixed mathematical and engineering contract for the one V2 candidate calibration
artifact selected in ADR-0007. This document is intentionally pre-implementation. It does not
create source code, typed models, fixtures, labels, manifests, artifacts, or assessments.

## Input boundary

The later fitter may consume only a verified V2 calibration-manifested fixture-set. For each
calibration observation, it may join:

```text
conditional_survival_confidence
observed_acceptance
```

after the runtime and expected-outcome assets have been independently validated and aligned.

The fitter must not accept:

```text
final_evaluation evidence
development evidence
adversarial-regression evidence
V1 data-bearing assets
candidate token IDs as model features
workload labels as model features
position indices as model features
capacity fields as model features
```

## Transform

For raw confidence `p`:

```text
epsilon=0.000001
p_clipped=min(max(p, epsilon), 1-epsilon)
z=log(p_clipped/(1-p_clipped))
calibrated_confidence=sigmoid(slope*z+intercept)
```

The implementation must preserve finite values strictly inside the open probability interval.

## Parameter contract

```text
slope_lower_bound=0.25
slope_upper_bound=4.00
intercept_lower_bound=-4.00
intercept_upper_bound=4.00
monotonicity_requirement=slope_positive
parameter_scope=global_only
```

No additional parameter is permitted without a new ADR and new V2 evidence protocol.

## Objective and deterministic optimizer

```text
objective=mean_binary_negative_log_likelihood
regularization_strength=0.01
regularization_expression=0.01*((slope-1.0)^2+intercept^2)
optimizer_id=deterministic_projected_gradient_descent_v1
initial_slope=1.0
initial_intercept=0.0
learning_rate=0.05
maximum_iterations=4000
convergence_tolerance=0.0000000001
gradient_norm_tolerance=0.00000001
tie_handling=retain_earlier_iteration_when_objective_difference_is_within_tolerance
```

Each iteration must:

1. calculate the objective and gradients from the calibration split only;
2. update both parameters from the fixed learning rate;
3. project `slope` and `intercept` into their declared bounds;
4. retain the best strictly lower objective;
5. stop only under the fixed convergence rule or maximum iteration bound.

No grid search, random restart, adaptive hyperparameter schedule, workload branch, or
final-evaluation feedback is allowed.

## Determinism and provenance controls

The future artifact must retain:

```text
optimizer_id
learning_rate
maximum_iterations
convergence_tolerance
gradient_norm_tolerance
regularization_strength
confidence_clipping_epsilon
initial_slope
initial_intercept
slope_bounds
intercept_bounds
fit_iteration_count
converged
calibration_manifest_aggregate_sha256
fit_case_ids
fit_scenario_family_ids
```

The future report must retain its source-code-visible failure state and must never discard an
optimizer failure or convergence failure.

## Output boundary

The artifact output is a calibrated probability only. It must not contain:

```text
verification decision
scheduler action
threshold
policy configuration
capacity action
utility score
promotion decision
final-evaluation label
```

The artifact remains:

```text
final_evaluation_accessed=false
runtime_control_eligible=false
```

until a later V2 final-evaluation assessment has completed and passed the separately frozen gate.

## Required implementation tests

Before V2 fitting is permitted, implementation tests must prove:

1. `slope > 0` yields a monotonic transform over a fixed confidence grid.
2. confidence clipping prevents infinite logits at zero and one.
3. parameter projection retains values within the declared bounds.
4. identical verified V2 calibration inputs produce byte-equivalent serialized artifacts.
5. final-manifested fixture sets are rejected by the fitter before labels are read.
6. V1 manifests, outcomes, artifacts, and assessment reports are not accepted as V2 fitter inputs.
7. no runtime output contains a policy action or promotion field.

## Non-claims

This candidate specification does not claim that the method is more accurate, more calibrated,
more useful, or safer than any earlier artifact. It is a precommitted contract that makes a later
V2 assessment interpretable.
