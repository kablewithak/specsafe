# ADR-0007: Select Bounded Global Platt Scaling for V2

- **Status:** Accepted
- **Date:** 2026-07-02
- **Decision scope:** `synthetic-calibration-redesign-v2`
- **Candidate artifact:** `bounded-platt-scaling-v1`
- **Supersedes:** No V1 artifact, manifest, assessment, or closure record.
- **Depends on:** ADR-0006 and the V2 method-selection gate.

## Context

`synthetic-calibration-redesign-v1` is closed as a reproducible negative result. Its held-out
evidence, artifacts, manifests, and reports are audit-only and cannot supply numerical targets,
fixture designs, parameter choices, or acceptance-criterion changes for V2.

ADR-0006 requires one candidate method to be selected and fully constrained before V2 runtime
inputs or expected outcomes are authored. The selection must be based on mathematical form,
deterministic local implementation, monotonicity, and compatibility with the V2 evidence floor.
It must not be a reaction to any V1 case, confidence, label, metric value, bin occupancy, or
held-out trace shape.

## Decision

SpecSafe selects one V2 candidate artifact:

```text
artifact_id=bounded-platt-scaling-v1
artifact_version=1.0.0
method_family=global_regularized_logistic_calibration
fit_split=calibration
fit_data_role=calibration
runtime_control_eligible=false
```

The artifact maps a raw conditional-survival confidence `p` to calibrated confidence `q`:

```text
p_clipped = min(max(p, 0.000001), 0.999999)
z = log(p_clipped / (1 - p_clipped))
q = sigmoid(slope * z + intercept)
```

The method has exactly two fitted global parameters:

```text
slope in [0.25, 4.00]
intercept in [-4.00, 4.00]
```

The positive slope bound preserves a monotonic increasing mapping and therefore preserves
confidence ordering. There are no workload, position, request, scenario-family, capacity, or
subgroup parameters.

## Frozen fit procedure

The V2 fitter must use only the verified V2 calibration manifest and post-hoc calibration labels.
The procedure is fixed before V2 fixture authoring:

```text
objective=mean_binary_negative_log_likelihood
regularization=0.01 * ((slope - 1.0)^2 + intercept^2)
optimizer=deterministic_projected_gradient_descent_v1
initial_slope=1.0
initial_intercept=0.0
learning_rate=0.05
maximum_iterations=4000
convergence_tolerance=0.0000000001
gradient_norm_tolerance=0.00000001
confidence_clipping_epsilon=0.000001
```

At every update, the fitter must project values into the declared parameter bounds. It must retain
the best strictly lower objective value seen so far. When objective values are equal within the
convergence tolerance, it must retain the earlier iteration. It must not select a different
optimizer, learning rate, regularization value, bound, iteration count, fallback, or candidate
after V2 outcomes are available.

## Why this method was selected

Bounded global Platt scaling is selected because it is:

- a two-parameter, globally shared, strictly monotonic transform;
- locally implementable with no remote service, external training set, or provider dependency;
- deterministic under the declared initialization, update rule, bounds, and tie handling;
- serializable as a small typed artifact with explicit provenance;
- expressive enough to model both global logit scaling and global offset while remaining more
  constrained than subgroup calibration, position-specific calibration, or nonparametric fitting.

This is a design decision. It does not claim the candidate will improve V2 calibration or pass the
V2 held-out promotion gate.

## Rejected alternatives

### Reuse `logit-temperature-scaling-v1`

Not selected. A temperature-only transform has no independently fitted intercept. This is a
mathematical capability distinction, not a ranking based on V1 held-out values.

### Isotonic regression

Not selected. Its nonparametric stepwise form introduces greater flexibility and fit-shape
dependence than is justified for the initial V2 controlled experiment.

### Beta calibration

Not selected. Its additional feature transformation and parameterization add complexity beyond
the minimum controlled V2 candidate.

### Workload-specific or position-specific calibration

Not selected. Such parameters require a separately approved subgroup evidence design and are
prohibited by the V2 method-selection gate.

### Method tournament or post-label candidate search

Not selected. Selecting among candidates after V2 labels exist would undermine the new
calibration/final-evaluation split boundary.

## Required artifact and report contracts

The later implementation must introduce V2-specific strict contracts. At minimum, the artifact
must retain:

```text
schema_version
artifact_id
artifact_version
fixture_set_id
fixture_set_version
calibration_manifest_aggregate_sha256
source_type
fit_split
fit_data_role
fit_case_ids
fit_scenario_family_ids
sample_count
positive_label_count
negative_label_count
slope
intercept
objective_value
optimizer_id
regularization_strength
confidence_clipping_epsilon
parameter_bounds
final_evaluation_accessed=false
runtime_control_eligible=false
```

The later fit report must retain the same provenance plus iteration count, convergence status,
failure status where applicable, and explicit non-promotion wording until a separate held-out
assessment occurs.

## Failure taxonomy

The later implementation must preserve typed failure states at least for:

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

A fitting failure is evidence. It must not trigger a search for a new optimizer, regularization
value, parameter bound, or fallback using the same V2 fixture set.

## Consequences

### Permitted next work

After this ADR is merged, the next permitted slice is a V2 scenario-family registry proposal.
It may reserve case identifiers and source-template fingerprints, but it must not author V2
runtime inputs, expected outcomes, manifests, fit code, or assessment code.

### Forbidden next work

This decision does not authorize:

- V2 fixture authoring;
- V2 fitting or evaluation;
- V2 manifest generation;
- adaptive scheduling, capacity profiles, utility scoring, or runtime control;
- claims that V2 improves calibration or is fit for automated verification scheduling.

## Evidence quarantine statement

No V1 numeric, example-level, or data-bearing asset determined this selection. V1 is referenced
only as the categorical fact that it was closed and not promoted. V2 remains a separate governed
experiment, not an in-place repair.
