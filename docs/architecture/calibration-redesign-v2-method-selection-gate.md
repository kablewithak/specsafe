# Calibration Redesign V2 Method-Selection Gate

## Purpose

Select exactly one V2 candidate calibration method before any
`synthetic-calibration-redesign-v2` runtime input or expected-outcome asset is authored.

This gate exists to prevent a second round of method selection after V2 outcomes become known.

## Decision state

```text
candidate_method_status=selected
candidate_artifact_id=bounded-platt-scaling-v1
candidate_artifact_version=1.0.0
method_family=global_regularized_logistic_calibration
method_search_status=closed_for_v2
v2_fixture_authoring_status=blocked_pending_registry_authoring
v2_fitting_status=blocked_pending_manifest_verified_calibration_evidence
```

The selected candidate is defined by ADR-0007 and
`docs/architecture/calibration-redesign-v2-bounded-platt-scaling-spec.md`.

## Selected candidate contract

```text
input_contract_version=calibration-redesign-v2-runtime-outcomes-v1
output_contract_version=bounded-platt-scaling-artifact-v1
fit_split=calibration
fit_data_role=calibration
objective=mean_binary_negative_log_likelihood_with_fixed_l2_regularization
optimizer=deterministic_projected_gradient_descent_v1
parameters=slope,intercept
slope_bounds=[0.25,4.00]
intercept_bounds=[-4.00,4.00]
confidence_clipping_epsilon=0.000001
monotonicity_guarantee=positive_global_slope
serialization=typed_json_artifact_with_manifest_provenance
```

## Allowed decision inputs

The decision used only:

- the method's published mathematical form and implementation complexity;
- monotonicity and deterministic serialization properties;
- compatibility with strict typed contracts and local reproducibility;
- the fixed V2 evidence floors and split-isolation requirements;
- the categorical historical fact that V1 was not promoted.

## V1 quarantine statement

The decision did not use:

```text
V1 Brier score values
V1 ECE values
V1 confidence values
V1 labels
V1 case IDs, trace IDs, token IDs, or prefix sequences
V1 final-family trace shapes
V1 bin occupancy
V1 artifact temperature
V1 fit-search output
```

`bounded-platt-scaling-v1` is not selected as a repair for a specific V1 metric movement.
It is selected as a bounded, global, two-parameter candidate whose behavior is fully fixed
before V2 evidence exists.

## Considered alternatives

| Alternative | Decision | Reason independent of V1 held-out values |
|---|---|---|
| Temperature-only scaling | Not selected | Does not include an independently fitted global intercept. |
| Isotonic regression | Not selected | Nonparametric fit shape is more flexible than the initial V2 evidence boundary permits. |
| Beta calibration | Not selected | Adds feature transformation and parameter complexity beyond the minimum controlled candidate. |
| Subgroup, workload, or position calibration | Not selected | Requires a separately approved subgroup evidence design. |
| Post-label method tournament | Not selected | Would make V2 outcome labels a method-selection input. |

## Fixed failure taxonomy

The later V2 implementation must retain at least:

```text
untrusted_v2_calibration_fixture_set
non_calibration_evidence
insufficient_calibration_evidence
degenerate_label_distribution
non_finite_confidence
non_finite_objective
optimizer_did_not_converge
artifact_schema_error
artifact_provenance_mismatch
```

## Decision acceptance checklist

This gate is accepted because:

1. One candidate artifact is named and versioned.
2. Its fit procedure and parameter constraints are fixed.
3. Its input and output contract requirements are specified.
4. Its failure modes are typed.
5. The decision explicitly records V1 evidence quarantine.
6. No V2 runtime or outcome files have been authored.
7. No V2 source code implements fitting or assessment.
8. The next allowed slice is a V2 scenario-family registry proposal, not a fit.

## Non-claims

This gate does not claim that the candidate is better than V1, calibrated, promotable, or fit for
automation. It is a governance decision that makes future evidence interpretable.
