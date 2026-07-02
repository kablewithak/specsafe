# Calibration Redesign V2 Method-Selection Gate

## Purpose

Select exactly one V2 candidate calibration method before any
`synthetic-calibration-redesign-v2` runtime input or expected-outcome asset is authored.

This gate exists to prevent a second round of method selection after V2 outcomes become known.

## Current decision state

```text
candidate_method_status=not_selected
method_search_status=not_authorized
v2_fixture_authoring_status=blocked_pending_method_selection
v2_fitting_status=blocked_pending_method_selection
```

No candidate is selected by this document.

## Allowed decision inputs

The decision owner may use:

- a method's published mathematical form and implementation complexity;
- monotonicity and deterministic serialization properties;
- compatibility with strict typed contracts and local reproducibility;
- the fixed V2 evidence floors and split-isolation requirements;
- the categorical historical fact that V1 was not promoted.

## Prohibited decision inputs

The decision owner must not use V1 numeric or example-level evidence to select a V2 method:

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

The method decision must not be justified as an attempt to reverse a specific V1 held-out
metric movement.

## Required decision record

A future candidate-method decision document must contain:

```text
candidate_artifact_id
candidate_artifact_version
method_family
input_contract_version
output_contract_version
fit_split=calibration
fit_data_role=calibration
objective
optimizer_or_closed_form_procedure
parameter_constraints
confidence_domain_and_clipping
monotonicity_guarantee
determinism_controls
serialization_schema
fixed_failure_taxonomy
why_v1_outcomes_did_not_determine_the_choice
```

It must also list considered alternatives and reject each without using V1 held-out values as
a ranking target.

## Forbidden candidate characteristics

The V2 entry gate rejects a candidate that requires any of the following before V2 fixture
authoring:

- selecting among several methods after reading V2 labels;
- workload-specific, position-specific, or subgroup parameters without a separately approved
  evidence design;
- unbounded hyperparameter search;
- final-evaluation feedback in a fit or fallback path;
- runtime scheduling behavior embedded in the calibrator;
- opaque external training data;
- remote service dependency or provider-specific state;
- nondeterministic serialization or non-reproducible fitting.

## Decision acceptance checklist

The method-selection gate is accepted only when:

1. One candidate artifact is named and versioned.
2. Its fit procedure and parameter constraints are fixed.
3. Its input and output contracts are specified.
4. Its failure modes are typed.
5. The decision explicitly records V1 evidence quarantine.
6. No V2 runtime or outcome files have been authored.
7. No V2 source code implements fitting or assessment yet.
8. The next allowed slice is a V2 scenario-family registry proposal, not a fit.

## Non-claims

This gate does not claim that a candidate is better than V1, calibrated, promotable, or fit for
automation. It is a governance decision that makes future evidence interpretable.
